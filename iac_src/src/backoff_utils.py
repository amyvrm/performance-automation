import time
import random
import requests

def exponential_backoff_sleep(attempt, base_delay=2, max_delay=60, jitter=True):
    delay = min(base_delay * (2 ** attempt), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random())
    time.sleep(delay)
    return delay

def retry_with_backoff(func, max_attempts=5, base_delay=2, max_delay=60, exceptions=(Exception,), success_check=None):
    last_exception = None
    for attempt in range(max_attempts):
        try:
            result = func()
            if success_check is None or success_check(result):
                if attempt > 0:
                    print(f"✓ Operation succeeded on attempt {attempt + 1}/{max_attempts}")
                return result
            print(f"Success check failed on attempt {attempt + 1}/{max_attempts}")
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                delay = exponential_backoff_sleep(attempt, base_delay, max_delay, jitter=True)
                print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}. Retrying in {delay:.2f}s...")
            else:
                print(f"All {max_attempts} attempts exhausted.")
                raise
        if attempt < max_attempts - 1:
            delay = exponential_backoff_sleep(attempt, base_delay, max_delay, jitter=True)
            print(f"Waiting {delay:.2f}s before retry {attempt + 2}/{max_attempts}...")
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry loop exited unexpectedly without success or exception")

def probe_endpoint_readiness(url, max_attempts=30, timeout=5, expected_status=200, check_content=None, initial_wait=2):
    """
    Probe HTTP endpoint until ready with latency tracking.
    Returns dict with readiness info and latency metrics.
    
    Args:
        initial_wait: Wait this many seconds before first probe (allows server startup)
    """
    # Initial wait for server startup
    if initial_wait > 0:
        print(f"→ Waiting {initial_wait}s for server startup before first probe...")
        time.sleep(initial_wait)
    
    latencies = []
    first_byte_times = []
    for attempt in range(max_attempts):
        start = time.time()
        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            first_byte_time = time.time() - start
            first_byte_times.append(first_byte_time)
            content = resp.text
            total_latency = time.time() - start
            latencies.append(total_latency)
            status_ok = resp.status_code == expected_status
            content_ok = check_content is None or check_content in content
            if status_ok and content_ok:
                return {
                    'ready': True,
                    'attempts': attempt + 1,
                    'avg_latency_ms': round(sum(latencies) / len(latencies) * 1000, 2),
                    'avg_ttfb_ms': round(sum(first_byte_times) / len(first_byte_times) * 1000, 2),
                    'last_status': resp.status_code
                }
            delay = min(3 * (2 ** attempt), 20)  # Increased base multiplier and max delay
            print(f"→ Probe succeeded (status {resp.status_code}) but content check failed. Waiting {delay}s before retry...")
            time.sleep(delay)
        except Exception as e:
            print(f"✗ Probe attempt {attempt + 1} failed: {e}")
            # Increase delay for failed probes to give server more time
            delay = min(4 * (2 ** attempt), 25)
            if attempt < max_attempts - 1:
                print(f"→ Waiting {delay}s before next probe...")
                time.sleep(delay)
    
    return {
        'ready': False,
        'attempts': max_attempts,
        'avg_latency_ms': round(sum(latencies) / len(latencies) * 1000, 2) if latencies else None,
        'avg_ttfb_ms': round(sum(first_byte_times) / len(first_byte_times) * 1000, 2) if first_byte_times else None
    }

def wait_for_nginx_ready(target_ip, max_wait=180):
    test_url = f"http://{target_ip}/test.htm"
    print(f"Probing {test_url} for readiness...")
    result = probe_endpoint_readiness(
        url=test_url,
        max_attempts=int(max_wait / 2),
        timeout=10,
        expected_status=200
    )
    if result['ready']:
        print(f"✓ Nginx ready after {result['attempts']} probes. "
              f"Avg TTFB: {result['avg_ttfb_ms']}ms, Latency: {result['avg_latency_ms']}ms")
    else:
        print(f"✗ Nginx not ready after {max_wait}s")
    return result
