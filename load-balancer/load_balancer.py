import asyncio
import websockets
import rpyc
import os

RPYC_SERVERS = [
    {"host": "wordcount_server_1", "port": 18812, "connections": 0},
    {"host": "wordcount_server_2", "port": 18813, "connections": 0},
    {"host": "wordcount_server_3", "port": 18814, "connections": 0}
]

server_index = 0  # To keep track of round-robin index

def select_server_round_robin():
    global server_index
    server = RPYC_SERVERS[server_index]
    server_index = (server_index + 1) % len(RPYC_SERVERS)
    return server

def select_server_least_connections():
    return min(RPYC_SERVERS, key=lambda s: s["connections"])

async def get_server_health():
    health_statuses = []
    for server in RPYC_SERVERS:
        try:
            conn = rpyc.connect(server["host"], server["port"])
            health_status = conn.root.health_check()
            health_statuses.append(f"{server['host']}:{server['port']}|{health_status}")
            conn.close()
        except Exception as e:
            health_statuses.append(f"{server['host']}:{server['port']}|Error: {str(e)}")
    return ",".join(health_statuses)

async def clear_cache():
    for server in RPYC_SERVERS:
        try:
            conn = rpyc.connect(server["host"], server["port"])
            conn.root.clear_cache()
            conn.close()
        except Exception as e:
            print(f"Failed to clear cache on {server['host']}:{server['port']}: {e}")

async def handle_client(websocket, path):
    try:
        request = await websocket.recv()

        if request == "health_check":
            health_status = await get_server_health()
            await websocket.send(health_status)
            return
        
        if request == "clear_cache":
            await clear_cache()
            await websocket.send("Cache cleared")
            return

        fileName, keyword = request.split(",")
        load_balancing_algo = os.getenv('LOAD_BALANCING_ALGORITHM', "ROUND_ROBIN")

        if load_balancing_algo == "ROUND_ROBIN":
            server = select_server_round_robin()
        elif load_balancing_algo == "LEAST_CONNECTIONS":
            server = select_server_least_connections()

        conn = rpyc.connect(server["host"], server["port"])
        server["connections"] += 1
        word_count = conn.root.exposed_word_count(fileName, keyword)
        server["connections"] -= 1
        conn.close()

        server_info = f"{server['host']}:{server['port']}"
        print(f"Request for {fileName}, {keyword} handled by {server_info}")

        await websocket.send(f"{word_count}|{server_info}")

    except Exception as e:
        await websocket.send(f"Error: {str(e)}")

async def main():
    async with websockets.serve(handle_client, "load_balancer", 8765):
        print(f"Load balancer web socket server started.")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
