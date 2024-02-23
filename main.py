from aiofile import async_open
from aiopath import AsyncPath
import asyncio
from datetime import datetime
import logging
import names
import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

from exchange import main as exchange

logging.basicConfig(level=logging.INFO)


async def logging_exchange(message):
    dt = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    log_message = f"{dt} - {message}"
    log_file_path = AsyncPath("exchange_log.txt")

    if not await log_file_path.exists():
        async with async_open(log_file_path, mode="w") as file:
            pass

    async with async_open(log_file_path, mode="a") as file:
        await file.write(f"{log_message}\n")


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def send_to_client(self, message: str, ws: WebSocketServerProtocol):
        await ws.send(message)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.strip().startswith("exchange"):
                await logging_exchange(message)
                args = message.strip().removeprefix("exchange").split()
                result = await exchange(*args)
                await self.send_to_client(str(result), ws)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)
            logging.info(f"{ws.remote_address} closed.")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())