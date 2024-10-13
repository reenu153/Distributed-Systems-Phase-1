import asyncio
import websockets
import rpyc
import random

RPYC_SERVERS = [
    ("wordcount_server_1", 18812),
    ("wordcount_server_2", 18813),
    ("wordcount_server_3", 18814)
]

async def handle_client(websocket, path):
    try:
        request = await websocket.recv()
        print(f"Received request: {request}")

        fileName, keyword = request.split(",")

        server_host, server_port = random.choice(RPYC_SERVERS)

        conn = rpyc.connect(server_host, server_port)

        word_count = conn.root.exposed_word_count(fileName, keyword)

        await websocket.send(str(word_count))

        print(f"Sent result: {word_count}")

    except Exception as e:
        print(f"Error: {e}")
        await websocket.send(f"Error: {str(e)}")

async def main():
    print("here")
    async with websockets.serve(handle_client, "load_balancer", 8765):
        print("Load balancer web socket server started.")
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
