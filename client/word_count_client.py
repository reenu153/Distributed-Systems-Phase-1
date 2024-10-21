import argparse
import asyncio
import websockets
from utils import plot_metrics, plot_count, clear_cache

async def send_batch_request(pairs):
    uri = "ws://load_balancer:8765"
    async with websockets.connect(uri) as websocket:
        batch_request = ";".join([f"{fileName},{keyword}" for fileName, keyword in pairs])
        await websocket.send(batch_request)
        response = await websocket.recv()
        return response.split(";")

async def handle_batch_requests(pairs):
    normal_data = await send_batch_request(pairs)
    cache_data = await send_batch_request(pairs)

    latencies = []
    counts = []

    normal_results = []
    cache_results = []

    for idx, (normal, cache) in enumerate(zip(normal_data, cache_data)):
        word_count, server_info, latency = normal.split(",")
        keyword_filename = f"{pairs[idx][1]}-{pairs[idx][0]}"
        normal_results.append(f"Request handled for {keyword_filename} by {server_info}: Latency = {float(latency):.4f} ms, Word Count = {word_count}")
        counts.append((keyword_filename, int(word_count)))
        latencies.append((keyword_filename, float(latency), "Normal"))

        cache_word_count, server_info_cache, cache_latency = cache.split(",")
        cache_results.append(f"Cache hit handled for {keyword_filename} by {server_info_cache}: Cache Latency = {float(cache_latency):.4f} ms, Word Count = {cache_word_count}")
        latencies.append((keyword_filename, float(cache_latency), "Cache"))

    for result in normal_results:
        print(result)
    
    for result in cache_results:
        print(result)

    plot_metrics(latencies)
    plot_count(counts)

    await clear_cache()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Word Count Client")
    parser.add_argument('--num_requests', type=int, help="Number of keyword-filename pairs to process")
    parser.add_argument('--pairs', nargs='+', help="List of keyword-filename pairs, e.g., 'keyword1:filename1 keyword2:filename2'")
    args = parser.parse_args()

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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(handle_batch_requests(keyword_filename_pairs))
