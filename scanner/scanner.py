import asyncio
from asyncio import Queue, Semaphore
from time import time
from traceback import print_exception
from typing import Any
from webdriver_manager.chrome import ChromeDriverManager

import httpx
from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup, Tag
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from models.program import Program
from scanner.filters import Filter
from scanner.solana import SolanaClientImlp
from telegram.client import TelegramBot


class Scanner:

    _API_ENDPOINT = "https://api.mainnet-beta.solana.com"
    RENT_TOKEN = "SysvarRent111111111111111111111111111111111"
    PROGRAM_TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

    filters: list[Filter]
    telegram: TelegramBot
    client: AsyncClient
    impl_client: SolanaClientImlp

    def __init__(self, telegram: TelegramBot) -> None:
        self.filters = []
        self.telegram = telegram
        self.client = AsyncClient(self._API_ENDPOINT, timeout=100)
        self.impl_client = SolanaClientImlp(self._API_ENDPOINT, timeout=100)
        self._running = True
        self._blocks = Queue()
        self._last_deploys = []
        self.request_id = 1
        self.processed = 0
        self._cap_keypair = Keypair.from_base58_string(
            "5UZPR39o6Lb9aX1qwoeLANZmEdiecuDL2bzSw4JCU2AQxisp1udJbE3GR33Xa2QWo1rkH19jtw7eJvyecTei5DJr"
        )

    def add_filter(self, _filter: Filter) -> None:
        self.filters.append(_filter)

    async def _scan_block(self, block: dict[str, Any]) -> None:
        if not block:
            return
        try:
            res = self.search_for_deploys(block)
            print(f"Res {res}")
            for address in res:
                await self.parse_program(address)
        except Exception as e:
            print_exception(type(e), e, e.__traceback__)

    def search_for_deploys(self, block: dict[str, Any]) -> list[str]:
        res = []
        for tr in block["result"]["transactions"]:
            tr = tr["transaction"]
            accounts = tr["message"]["accountKeys"]
            for instr in tr["message"]["instructions"]:
                try:
                    _ac = instr["accounts"]
                    if len(_ac) == 2:
                        if (
                            accounts[instr["programIdIndex"]] == self.PROGRAM_TOKEN
                            and accounts[_ac[1]] == self.RENT_TOKEN
                        ):
                            program = accounts[_ac[0]]
                            if not program in self._last_deploys:
                                res.append(program)
                                self._last_deploys.append(program)
                finally:
                    continue
        return res
    
    async def _waiter(self, task):
        self._tasks += 1
        while not task.done():
            await asyncio.sleep(1)
        await self._scan_block(task.result())
        self._tasks -= 1

    async def realtime_chain_parse(self) -> None:
        proxies = [
            "http://3u3Dgb:pS6aB2@168.80.61.216:8000",
            "http://3u3Dgb:pS6aB2@45.148.246.61:8000",
            "http://xVxT79:7T2HEV@91.198.215.75:8000",
            "http://xVxT79:7T2HEV@91.198.215.196:8000",
            ""
        ]
        latest = (await self.impl_client.get_slot())["result"]
        self._tasks = 0
        while self._running:
            print("CHECKPOINT!")
            blocks = []
            while not blocks:
                try:
                    blocks = (await self.client.get_blocks(start_slot=latest)).value
                except Exception as e:
                    await asyncio.sleep(1)

            # amount = len(blocks) // len(proxies) if len(blocks) > len(proxies) else len(blocks)
            for i in range(len(blocks)):
                try:
                    task = self._loop.create_task(
                        self._realtime_chain_parse(blocks[i], proxies[i % len(proxies)])
                    )
                    self._loop.create_task(
                        self._waiter(task)
                    )
                except Exception as e:
                    print_exception(type(e), e, e.__traceback__)

            await asyncio.sleep(5)
            latest = blocks[-1]

    async def _realtime_chain_parse(self, slot: int, proxy: str) -> dict[str, Any]:
        async with ClientSession(connector=TCPConnector(verify_ssl=False), skip_auto_headers=["X-Forwarded-For", "Referer"]) as session:
            try:
                resp = await session.post(
                    url=self._API_ENDPOINT,
                    headers={"content-type": "application/json"},
                    json={
                        "jsonrpc": "2.0",
                        "id": self.request_id,
                        "method": "getBlock",
                        "params": [slot, {"maxSupportedTransactionVersion": 0}],
                    },
                    proxy=proxy if proxy else None,
                )
                try:
                    self.request_id += 1
                    res = await resp.json()
                    res["result"]
                except:
                    resp.close()
                else:
                    return res

            except Exception as e:
                print_exception(type(e), e, e.__traceback__)

    async def parse_program(self, address: str) -> Program:
        solscan_link = f"https://solscan.io/token/{address}"

        kwargs = {"title": "unnamed token"}

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
  
        driver.get(solscan_link+"#metadata")

        await asyncio.sleep(13)

        bs = BeautifulSoup(driver.page_source, features="html.parser")

        text = f"<a href=\"{solscan_link}\">Solscan.io</a> check:\n"

        for d in bs.find_all("div", attrs={"class": "variable-row"}):
            d: Tag
            if d.get_text().startswith("\"name"):
                kwargs["title"] = d.find("span", attrs={"class": "string-value"}).text.strip("\"")
            
            elif d.get_text().startswith("\"symbol"):
                kwargs["symbol"] = d.find("span", attrs={"class": "string-value"}).text.strip("\"")
            
            elif d.get_text().startswith("\"description"):
                kwargs["description"] = d.find("span", attrs={"class": "string-value"}).text.strip("\"")

            elif d.get_text().startswith("\"image"):
                kwargs["icon"] = d.find("span", attrs={"class": "string-value"}).text.strip("\"")

        img = bs.find("img", attrs={"width": "30px", "height": "auto"})
        if img:
            kwargs["icon"] = img.attrs["src"]

        for d in bs.find_all("div", attrs={"class": "ant-row"}):
            d: Tag
            if d.get_text().startswith("Price"):
                kwargs["price"] = d.children[1].get_text()

            if d.get_text().startswith("Market Cap"):
                kwargs["cap"] = d.children[1].get_text()

            if d.get_text().startswith("Current Supply"):
                kwargs["supply"] = d.children[1].get_text()

            if d.get_text().startswith("Website"):
                kwargs["website"] = d.children[1].get_text()

        text += f"<b>Coin:</b> <i>{kwargs['title']}</i>\n"
        text += f"<b>Address:</b> <code>{address}</code>\n"
        if kwargs.get("symbol"):
            text += f"<b>Symbol:</b> <code>{kwargs['symbol']}</code>\n"
        if kwargs.get("description"):
            text += f"<b>Description:</b> {kwargs['description']}\n"

        if kwargs.get("price"):
            text += f"<b>Price:</b> <code>{kwargs['price']}</code>\n"

        if kwargs.get("cap"):
            text += f"<b>Market cap:</b> <code>{kwargs['cap']}</code>\n"

        if kwargs.get("supply"):
            text += f"<b>Current Supply:</b> <code>{kwargs['currentSupply']}</code>\n"

        if kwargs.get("website"):
            text += f"<b>Website:</b> <code>{kwargs['website']}</code>\n"

        text += "\n\n"
        rugcheck_link = f"https://rugcheck.xyz/tokens/{address}"

        kwargs = {"title": "unnamed token"}

        driver.get(rugcheck_link)

        await asyncio.sleep(13)

        bs = BeautifulSoup(driver.page_source, features="html.parser")

        text = f"<a href=\"{solscan_link}\">Rugcheck.io</a> check:\n"

        main_d = bs.find("div", attrs={"class": "card-body"})
        total = main_d.find("h1")

        text += f"<b>Total check:</b> {total.getText()}\n\n"

        row = main_d.find("div", attrs={"class": "row"})
        for c, d in enumerate(row.find_all("div")):
            if c > 0:
                text += " | "
            text += f"<b>{d.getText()}</b>"

        await self.telegram.send(text, kwargs["icon"] if kwargs.get("icon") else None)
        driver.close()

    def run(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            self._loop.create_task(self.realtime_chain_parse())
            self._loop.run_forever()
        except Exception as e:
            print_exception(type(e), e, e.__traceback__)
            self._running = False
        finally:
            self._loop.close()
