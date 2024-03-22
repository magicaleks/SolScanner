import asyncio
from asyncio import Queue, Semaphore
from time import time
from traceback import print_exception
from typing import Any
from webdriver_manager.chrome import ChromeDriverManager

import httpx
from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup
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

    async def scan(self) -> None:
        # self._latest = (await self.impl_client.get_slot())["result"]
        while False:

            block = await self._blocks.get()
            # self.blocks_processed = 0

            # prd = len(blocks.value) // 3

            # self._loop.create_task(self._sub_scan(blocks.value[:prd]))
            # self._loop.create_task(self._sub_scan(blocks.value[prd:prd*2]))
            # self._loop.create_task(self._sub_scan(blocks.value[prd*2:]))

            # for slot in blocks.value:
            #

            self._loop.create_task(self._scan_block(block))

            # await asyncio.sleep(1)

            # await self._semaphore.acquire()
            # print(f"diff {len(blocks.value)-self.blocks_processed}")
            # if blocks.value:
            #     self._latest = blocks.value[-1]

    # async def _sub_scan(self, blocks) -> None:
    #     await self._semaphore.acquire()
    #     for slot in blocks:
    #         await self._scan_block(slot)
    #     self._semaphore.release()

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
        # print(block["result"]["parentSlot"])
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
        ]
        latest = (await self.impl_client.get_slot())["result"]
        self._tasks = 0
        while self._running:
            blocks = []
            while not blocks:
                try:
                    blocks = (await self.client.get_blocks(start_slot=latest)).value
                except Exception as e:
                    await asyncio.sleep(1)

            print(len(blocks), blocks[-1])
            print("Tasks "+str(self._tasks))
            t = time()
            amount = len(blocks) // len(proxies) if len(blocks) > len(proxies) else len(blocks)
            for c, p in enumerate(proxies):
                for slot in blocks[amount*c:amount*(c+1)]:
                    try:
                        task = self._loop.create_task(
                            self._realtime_chain_parse(slot, p)
                        )
                        self._loop.create_task(
                            self._waiter(task)
                        )
                    except Exception as e:
                        print_exception(type(e), e, e.__traceback__)
                    # await asyncio.sleep(0.1)

            await asyncio.sleep(20)
            latest = blocks[-1]

    async def _realtime_chain_parse(self, slot: int, proxy: str) -> dict[str, Any]:
        while self._running:
            try:
                async with ClientSession(connector=TCPConnector(verify_ssl=False), skip_auto_headers=["X-Forwarded-For", "Referer"]) as session:
                    async with session.post(
                        url=self._API_ENDPOINT,
                        headers={"content-type": "application/json"},
                        json={
                            "jsonrpc": "2.0",
                            "id": self.request_id,
                            "method": "getBlock",
                            "params": [slot, {"maxSupportedTransactionVersion": 0}],
                        },
                        proxy=proxy if proxy else None,
                    ) as resp:
                        self.request_id += 1
                        res = await resp.json()
                        if res.get("error"):
                            if res["error"]["code"] == 429:
                                await asyncio.sleep(10)
                                continue
                            print(res["error"])

                        return res

            except Exception as e:
                print_exception(type(e), e, e.__traceback__)

    async def parse_program(self, address: str) -> Program:
        link = f"https://solscan.io/token/{address}"
        # html = httpx.get(link)

        kwargs = {"title": "token unnamed", "address": address, "link": link, "cap": 0, "liq": 0}

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        driver.get(link)

        await asyncio.sleep(13)

        bs = BeautifulSoup(driver.page_source, features="html.parser")

        title = bs.find("title")
        if title:
            kwargs["title"] = title.get_text().split("|")[0].strip(" ")

        img = bs.find("img", attrs={"width": "30px", "height": "auto"})
        if img:
            kwargs["icon"] = img.attrs["src"]

        await self.telegram.send(Program(**kwargs))
        driver.close()

    def run(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            self._loop.create_task(self.realtime_chain_parse())
            self._loop.create_task(self.scan())
            # self._loop.create_task(self.parse_program("8ivhyrs36K82Mko4oPQxUCZiSDxv4Rwb5AAr1pDFKpQp"))
            self._loop.run_forever()
        except Exception as e:
            print_exception(type(e), e, e.__traceback__)
        finally:
            self._loop.close()
