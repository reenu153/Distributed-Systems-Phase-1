import argparse
import asyncio
import websockets
import matplotlib
matplotlib.use('Agg')
import time
import matplotlib.pyplot as plt
import numpy as np
import os

DEFAULT_FILENAME = "defaultfile"
DEFAULT_KEYWORD = "defaultkeyword"

async def send_word_count_request(fileName, keyword):
    uri = "ws://load_balancer:8765"
    async with websockets.connect(uri) as websocket:
        request = f"{fileName},{keyword}"
        await websocket.send(request)
        response = await websocket.recv()
        
        try:
            result, server_info = response.split("|")
            if "Text file" in result:
                return result, server_info
            return int(result), server_info
        except ValueError:
            return None, None

async def clear_cache():
    uri = "ws://load_balancer:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("clear_cache")
        response = await websocket.recv()
        print(response)

async def serve_warmup(filename, keyword):
    result, server_info = await send_word_count_request(filename, keyword)
    if result is None:
        print("Warm-up request failed.\n")
    else:
        print(f"Warm-up request succeeded: {result} from {server_info}")

async def get_server_health():
    uri = "ws://load_balancer:8765"
    async with websockets.connect(uri) as websocket:
        request = "health_check"
        await websocket.send(request)
        response = await websocket.recv()
        
        servers = response.split(",")
        for server_info in servers:
            try:
                server, status = server_info.split("|")
                print(f"{server}: {status}")
            except ValueError:
                pass

async def monitor_server_health():
    try:
        while True:
            await get_server_health()
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("\nStopping health monitoring...")

async def handle_batch_requests(pairs):
    try:
        first_filename, first_keyword = pairs[0]
        await serve_warmup(first_filename, first_keyword)
        await clear_cache()
        
        latencies = []
        counts = []

        for filename, keyword in pairs:
            start_time = time.time()
            word_count, server_info = await send_word_count_request(filename, keyword)

            if word_count is None or isinstance(word_count, str):
                continue

            latency = (time.time() - start_time) * 1000
            print(f"First request handled by {server_info}: Latency = {latency:.4f} ms, Word Count = {word_count}")

            start_time_cache = time.time()
            cache_word_count, server_info_cache = await send_word_count_request(filename, keyword)

            if cache_word_count is None or isinstance(cache_word_count, str):
                continue

            cache_latency = (time.time() - start_time_cache) * 1000
            print(f"Cache hit handled by {server_info_cache}: Cache Latency = {cache_latency:.4f} ms")

            latencies.append((f"{keyword}-{filename}", latency, cache_latency))
            counts.append((f"{keyword}-{filename}", word_count))

        plot_metrics(latencies)
        plot_count(counts)

        # Clear cache after batch request
        await clear_cache()

    except Exception as e:
        print(f"Error: {e}")

def plot_metrics(latencies):
    x_labels = [pair[0] for pair in latencies]
    normal_latencies = [pair[1] for pair in latencies]
    cache_latencies = [pair[2] for pair in latencies]

    x = np.arange(len(x_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, normal_latencies, width, label='Normal Latency')
    bars2 = ax.bar(x + width/2, cache_latencies, width, label='Cache Latency')

    ax.set_xlabel("Keyword-Filename Pair")
    ax.set_ylabel("Latency (milliseconds)")
    ax.set_title("Normal Latency vs Cache Latency (ms) for Keyword-Filename Pairs")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45)
    ax.legend()

    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig("/output/latency_plot.png")
    print("Plot saved as /output/latency_plot.png")

def plot_count(counts):
    x_labels = [pair[0] for pair in counts]
    count_values = [pair[1] for pair in counts]

    x = np.arange(len(x_labels))

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(x, count_values, width=0.5, color='green')

    ax.set_xlabel("Keyword-Filename Pair")
    ax.set_ylabel("Word Count")
    ax.set_title("Word Count for Each Keyword-Filename Pair")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig("/output/count.png")
    print("Plot saved as /output/count.png")

# Argument Parsing Outside Main Loop
parser = argparse.ArgumentParser(description="Word Count Client")
parser.add_argument('--num_requests', type=int, help="Number of keyword-filename pairs to process")
parser.add_argument('--pairs', nargs='+', help="List of keyword-filename pairs, e.g., 'keyword1:filename1 keyword2:filename2'")
args = parser.parse_args()

# Prepare Pairs Based on Args
keyword_filename_pairs = []
if args.num_requests and args.pairs:
    if len(args.pairs) != args.num_requests:
        print("Number of pairs provided does not match num_requests")
        exit(1)

    for pair in args.pairs:
        try:
            keyword, filename = pair.split(":")
            keyword_filename_pairs.append((filename, keyword))
        except ValueError:
            print(f"Invalid format for pair: {pair}. Expected 'keyword:filename'")
            exit(1)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if keyword_filename_pairs:
            loop.create_task(monitor_server_health())  # Start health monitoring
            loop.run_until_complete(handle_batch_requests(keyword_filename_pairs))
        else:
            # Execute Default Warm-up
            loop.create_task(monitor_server_health())  # Start health monitoring
            loop.run_until_complete(serve_warmup(DEFAULT_FILENAME, DEFAULT_KEYWORD))
    except KeyboardInterrupt:
        print("\nExiting...")
