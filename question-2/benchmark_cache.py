"""
Measures a cache MISS (first call) vs cache HIT (repeated identical call)
against the running spam-detection API. Run this against the Compose stack:

    docker compose up -d
    python3 benchmark_cache.py

It sends the same text 1 + N times, using the server's own wall-clock
`X-Request-Duration` measurement, and separately the client-observed
round-trip time, so the results aren't an artifact of network jitter alone.
"""
import statistics
import sys
import time

import requests

API_URL = "http://localhost:8000/predict"
TEXT = "WIN a FREE iPhone now! Click here: bit.ly/xyz123"
REPEATS = 10


def call(text):
    t0 = time.perf_counter()
    resp = requests.post(API_URL, json={"text": text}, timeout=5)
    client_ms = (time.perf_counter() - t0) * 1000
    body = resp.json()
    return body["label"], body["cached"], body["latency_ms"], client_ms


def main():
    print(f"Target: {API_URL}")
    print(f"Text:   {TEXT!r}\n")

    label, cached, server_ms, client_ms = call(TEXT)
    print(f"Call  1 (expect MISS): label={label:5s} cached={cached!s:5s} "
          f"server={server_ms:7.3f} ms  client={client_ms:7.3f} ms")
    miss_server, miss_client = server_ms, client_ms

    hit_server_times, hit_client_times = [], []
    for i in range(2, REPEATS + 1):
        label, cached, server_ms, client_ms = call(TEXT)
        hit_server_times.append(server_ms)
        hit_client_times.append(client_ms)
        print(f"Call {i:2d} (expect HIT):  label={label:5s} cached={cached!s:5s} "
              f"server={server_ms:7.3f} ms  client={client_ms:7.3f} ms")

    avg_hit_server = statistics.mean(hit_server_times)
    avg_hit_client = statistics.mean(hit_client_times)

    print("\n--- Summary ---")
    print(f"Cache MISS (call 1):        server={miss_server:.3f} ms   client={miss_client:.3f} ms")
    print(f"Cache HIT  (avg of {REPEATS - 1}):    server={avg_hit_server:.3f} ms   client={avg_hit_client:.3f} ms")
    print(f"Server-side speedup: {miss_server / avg_hit_server:.1f}x faster on cache hit")
    print(f"Client-side speedup: {miss_client / avg_hit_client:.1f}x faster on cache hit")

    if avg_hit_server >= miss_server:
        print("\nWARNING: cache hits were not faster than the miss -- check that Redis is reachable.")
        sys.exit(1)


if __name__ == "__main__":
    main()
