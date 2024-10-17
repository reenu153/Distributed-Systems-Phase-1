import asyncio
import websockets
import rpyc
import random
import os

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

def select_server_least_connections():
    return min(RPYC_SERVERS, key=lambda s: s["connections"])

async def handle_client(websocket, path):
    try:
        request = await websocket.recv()
        print(f"Received request: {request}")

        fileName, keyword = request.split(",")

        load_balancing_algo = os.getenv('LOAD_BALANCING_ALGORITHM',"ROUND_ROBIN")
        if load_balancing_algo == "ROUND_ROBIN":
            server = select_server_round_robin()
        elif load_balancing_algo == "LEAST_CONNECTIONS":
            server = select_server_least_connections()

        print(f"Connection opened to " + server["host"] + " listening on port " + str(server["port"]))

        conn = rpyc.connect(server["host"], server["port"])

        server["connections"] += 1

        word_count = conn.root.exposed_word_count(fileName, keyword)

        server["connections"] -= 1

        print(f"Connection to "+server["host"]+" on "+str(server["port"])+" closed")

        await websocket.send(str(word_count))

        print(f"Sent result: {word_count}")

    except Exception as e:
        print(f"Error: {e}")
        await websocket.send(f"Error: {str(e)}")

async def main():
    async with websockets.serve(handle_client, "load_balancer", 8765):
        print(f"Load balancer web socket server started.")
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
