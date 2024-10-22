import asyncio
import websockets
import rpyc
import os
import time
import random

RPYC_SERVERS = [
    {"host": "wordcount_server_1", "port": 18812},
    {"host": "wordcount_server_2", "port": 18813},
    {"host": "wordcount_server_3", "port": 18814}
]

server_index = 0

def select_server_round_robin():
    global server_index
    server = RPYC_SERVERS[server_index]
    server_index = (server_index + 1) % len(RPYC_SERVERS)
    return server

def select_server_random():
    return RPYC_SERVERS[random.randint(0, len(RPYC_SERVERS) - 1)]

async def process_request(filename, keyword):
    load_balancing_algo = os.getenv('LOAD_BALANCING_ALGORITHM', "ROUND_ROBIN")
    
    if load_balancing_algo == "RANDOM":
        server = select_server_random()
    else:
        server = select_server_round_robin()

    print(f"Connection opened to " + server["host"] + " listening on port " + str(server["port"]))

    conn = await asyncio.to_thread(rpyc.connect, server["host"], server["port"])
    
    start_time = time.time()
    word_count = await asyncio.to_thread(conn.root.exposed_word_count, filename, keyword)
    latency = (time.time() - start_time) * 1000

    conn.close()
    print(f"Connection to "+server["host"]+" on "+str(server["port"])+" closed")

    return f"{word_count},{server['host']}:{server['port']},{latency}"

async def handle_client(websocket, path):
    try:
        request = await websocket.recv()
        if request == "clear_cache":
            await clear_cache_on_all_servers()
            await websocket.send("Cache cleared on all servers")
            return

        filename, keyword = request.split(",")
        result = await process_request(filename, keyword)

        await websocket.send(result)

    except Exception as e:
        await websocket.send(f"Error occurred: {str(e)}")

async def clear_cache_on_all_servers():
    tasks = [asyncio.to_thread(rpyc.connect, server["host"], server["port"]) for server in RPYC_SERVERS]
 
    connections = await asyncio.gather(*tasks)
    
    for conn in connections:
        await asyncio.to_thread(conn.root.clear_cache)
        conn.close()

async def main():
    async with websockets.serve(handle_client, "load_balancer", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())