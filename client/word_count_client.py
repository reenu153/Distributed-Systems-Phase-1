import argparse
import asyncio
import websockets
from utils import plot_metrics, plot_count, clear_cache

async def send_request(filename, keyword):
    uri = "ws://load_balancer:8765"
    async with websockets.connect(uri) as websocket:
        request = f"{filename},{keyword}"
        await websocket.send(request)
        response = await websocket.recv()
        return response

async def handle_requests(pairs):
    latencies = []
    counts = []

    for filename, keyword in pairs:
        await asyncio.sleep(1)  # 1-second delay before processing each request
        
        normal_data = await send_request(filename, keyword)
        
        try:
            word_count, server_info, latency = normal_data.split(",")
        except ValueError:
            print(f"Unexpected response format: {normal_data}")
            continue
        
        keyword_filename = f"{keyword}-{filename}"
        normal_result = f"Request handled for {keyword_filename} by {server_info}: Latency = {float(latency):.4f} ms, Word Count = {word_count}"
        print(normal_result)
        counts.append((keyword_filename, int(word_count)))
        latencies.append((keyword_filename, float(latency), "Normal"))

        cache_data = await send_request(filename, keyword)

        try:
            cache_word_count, server_info_cache, cache_latency = cache_data.split(",")
        except ValueError:
            print(f"Unexpected cache response format: {cache_data}")
            continue
        
        cache_result = f"Cache hit handled for {keyword_filename} by {server_info_cache}: Cache Latency = {float(cache_latency):.4f} ms, Word Count = {cache_word_count}"
        print(cache_result)
        latencies.append((keyword_filename, float(cache_latency), "Cache"))

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
    loop.run_until_complete(handle_requests(keyword_filename_pairs))