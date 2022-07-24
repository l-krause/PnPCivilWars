import asyncio
import websockets
import json

CHARACTERS = ["configs/manollo.json", "configs/thork.json", "configs/martha.json", "configs/bart.json"]


async def chooseCharacter(message, websocket):
    await websocket.send()


async def handler(websocket):
    while True:
        message = await websocket.recv()
        message = json.loads(message)
        if message["action"] == "chooseCharacter":
            await chooseCharacter(message, websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
