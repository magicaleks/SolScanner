import base64
import sys
from typing import Any

import backoff
import httpx
from solathon.core.types import RPCResponse


class AsyncHTTPClient:
    """Asynchronous HTTP Client to interact with Solana JSON RPC"""

    def __init__(self, endpoint: str, timeout: float):
        self.endpoint = endpoint
        version = sys.version_info
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": (
                "SolScanner by Magicaleks " f"Python{version[0]} {version[1]}"
            ),
        }
        self.request_id = 0
        self.client = httpx.AsyncClient(timeout=timeout)
        self._running = False

    # @backoff.on_exception(
    #         wait_gen=backoff.fibo,
    #         exception=httpx.HTTPError,
    #         max_tries=8,
    # )
    async def send(self, data: dict[str, Any]) -> RPCResponse:
        resp = await self.client.post(
            url=self.endpoint, headers=self.headers, json=data
        )
        res = resp.json()
        if res.get("error"):
            raise httpx.HTTPError(res["error"]["message"])
        return res

    def build_data(self, method: str, params: list[Any]) -> dict[str, Any]:
        self.request_id += 1

        if isinstance(params[0], bytes):
            params[0] = base64.b64encode(params[0]).decode("utf-8")

        return {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params if params else None,
        }

    async def refresh(self) -> None:
        await self.client.aclose()
        self.request_id = 0
        self.client = httpx.AsyncClient()


class SolanaClientImlp:
    def __init__(self, endpoint: str | None = None, timeout: float = 10):
        self.http = AsyncHTTPClient(endpoint, timeout)
        self.endpoint = endpoint

    async def get_block(
        self, slot: int, *, max_supported_transaction_version: int | None = None
    ) -> RPCResponse:
        """
        Returns the block information for a given slot.

        Args:
        - slot (int): The slot of the block.

        Returns:
        - RPCResponse: The response from the Solana RPC server.
        """
        return await self.build_and_send_request_async(
            "getBlock",
            [
                slot,
                {"maxSupportedTransactionVersion": max_supported_transaction_version},
            ],
        )

    async def get_blocks(
        self,
        start_slot: int,
        end_slot: int | None = None,
        *,
        max_supported_transaction_version: int | None = None,
    ) -> RPCResponse:
        """
        Returns the block information for a range of slots.

        Args:
        - start_slot (int): The starting slot.
        - end_slot (int | None): The ending slot. Defaults to None.

        Returns:
        - RPCResponse: The response from the Solana RPC server.
        """
        params = [start_slot]
        if end_slot:
            params.append(end_slot)

        params.append(
            {"maxSupportedTransactionVersion": max_supported_transaction_version}
        )

        return await self.build_and_send_request_async("getBlocks", params)

    async def get_slot(self) -> RPCResponse:
        """
        Sends a request to the Solana RPC endpoint to retrieve the current slot.

        Returns:
            RPCResponse: The response from the RPC endpoint.
        """
        return await self.build_and_send_request_async("getSlot", [None])

    async def build_and_send_request_async(
        self, method: str, params: list[Any]
    ) -> RPCResponse:
        """
        Builds and sends an RPC request to the server.

        Args:
            method (Text): The RPC method to call.
            params (List[Any]): The parameters to pass to the RPC method.

        Returns:
            RPCResponse: The response from the server.
        """

        data: dict[str, Any] = self.http.build_data(method=method, params=params)
        res: RPCResponse = await self.http.send(data)
        return res
