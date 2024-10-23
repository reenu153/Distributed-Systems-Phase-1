import matplotlib.pyplot as plt
import numpy as np
import asyncio
import websockets

async def clear_cache():
    uri = "ws://load_balancer:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("clear_cache")
        response = await websocket.recv()
        print(response)

def plot_metrics(latencies):
    latency_dict = {}
    
    for pair, latency, label in latencies:
        if pair not in latency_dict:
            latency_dict[pair] = {"Normal": None, "Cache": None}
        latency_dict[pair][label] = latency
    
    xLabel = list(latency_dict.keys())
    normal_latencies = [latency_dict[pair]["Normal"] for pair in xLabel]
    cache_latencies = [latency_dict[pair]["Cache"] for pair in xLabel]

    x = np.arange(len(xLabel))
    width = 0.35

    fig, axis = plt.subplots(figsize=(10, 6))
    bars1 = axis.bar(x - width / 2, normal_latencies, width, label='Normal Latency')
    bars2 = axis.bar(x + width / 2, cache_latencies, width, label='Cache Latency')

    axis.set_xlabel("Keyword-Filename Pair")
    axis.set_ylabel("Latency (milliseconds)")
    axis.set_title("Normal Latency vs Cache Latency (ms) for Keyword-Filename Pairs")
    axis.set_xticks(x)
    axis.set_xticklabels(xLabel, rotation=45)
    axis.legend()

    for bar in bars1:
        height = bar.get_height()
        axis.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

    for bar in bars2:
        height = bar.get_height()
        axis.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig("/output/latency_plot.png")
    print("Plot saved as /output/latency_plot.png")

def plot_count(counts):
    xLabel = [pair[0] for pair in counts]
    count_values = [pair[1] for pair in counts]

    x = np.arange(len(xLabel))

    fig, axis = plt.subplots(figsize=(10, 6))

    bars = axis.bar(x, count_values, width=0.5, color='green')

    axis.set_xlabel("Keyword-Filename Pair")
    axis.set_ylabel("Word Count")
    axis.set_title("Word Count for Each Keyword-Filename Pair")
    axis.set_xticks(x)
    axis.set_xticklabels(xLabel, rotation=45)

    for bar in bars:
        height = bar.get_height()
        axis.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig("/output/count.png")
    print("Plot saved as /output/count.png")