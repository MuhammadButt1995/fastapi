import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(f"Received updated networking data: {json.loads(data)}")

asyncio.run(test_websocket())