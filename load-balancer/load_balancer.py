import asyncio
import websockets
import rpyc
import os
import time
import random

RPYC_SERVERS = [
    {"host": "wordcount_server_1", "port": 18812, "connections": 0},
    {"host": "wordcount_server_2", "port": 18813, "connections": 0},
    {"host": "wordcount_server_3", "port": 18814, "connections": 0}
]

server_index = 0

def select_server_round_robin():
    global server_index
    server = RPYC_SERVERS[server_index]
    server_index = (server_index + 1) % len(RPYC_SERVERS)
    return server

def select_server_random():
    return RPYC_SERVERS[random.randint(0,len(RPYC_SERVERS)-1)]

def process_request(fileName, keyword):
    load_balancing_algo = os.getenv('LOAD_BALANCING_ALGORITHM', "ROUND_ROBIN")

    if load_balancing_algo == "RANDOM":
        server = select_server_random()
        
    else:
        server = select_server_round_robin()

    conn = rpyc.connect(server["host"], server["port"])
    server["connections"] += 1

    start_time = time.time()
    word_count = conn.root.exposed_word_count(fileName, keyword)
    latency = (time.time() - start_time) * 1000

    server["connections"] -= 1
    conn.close()

    return f"{word_count},{server['host']}:{server['port']},{latency}"

async def handle_client(websocket, path):
    request = await websocket.recv()

    if request == "clear_cache":
        for server in RPYC_SERVERS:
            conn = rpyc.connect(server["host"], server["port"])
            conn.root.clear_cache()
            conn.close()
        await websocket.send("Cache cleared on all servers")
        return

    pairs = request.split(";")
    results = [process_request(*pair.split(",")) for pair in pairs]

    await websocket.send(";".join(results))

async def main():
    async with websockets.serve(handle_client, "load_balancer", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
