#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask web application to continuously display cAdvisor metrics (table and graphs)
for the 'open5gs' namespace. Fetches Kubernetes mappings only once on startup.
"""

import requests
import json
import sys
import subprocess
import re
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify
import math # For checking NaN

# --- Configuration ---
OPEN5GS_NAMESPACE = "open5gs"
CADVISOR_NAMESPACE = "cadvisor"
CADVISOR_PORT = 8080
# How often the background thread fetches stats (seconds)
COLLECTION_INTERVAL_SECONDS = 3.0
# Number of historical samples to keep for rate calculation AND graphing
HISTORY_SIZE = 20

# --- Global State ---
# Stores raw data for rate calculation:
# {container_id: deque([(timestamp_ns, cpu_total_ns), ...], maxlen=HISTORY_SIZE)}
container_history = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))
# Stores calculated data points for the API/graphs:
# {container_id: deque([(timestamp_sec, cpu_mcore, memory_mib), ...], maxlen=HISTORY_SIZE)}
api_metric_history = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))
# Lock for thread-safe access to histories
data_lock = threading.Lock()
# To signal the background thread to stop
stop_event = threading.Event()
# Store mappings globally - These will be populated once at startup
node_to_cadvisor_ip_map = {}
target_pods_on_nodes_map = {}

# --- Kubectl Interaction (Same as before) ---

def run_kubectl_command(command_args, parse_json=True):
    """Runs kubectl, returns parsed JSON or raw text output."""
    command = ['kubectl'] + command_args
    try:
        # Reduced timeout slightly as it runs only once at start
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout) if parse_json else result.stdout
    except FileNotFoundError:
        print("Error: 'kubectl' command not found.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl: {e}\nStderr: {e.stderr}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
         print(f"Error: kubectl command '{' '.join(command)}' timed out.", file=sys.stderr)
         return None
    except Exception as e:
        print(f"Unexpected kubectl error: {e}", file=sys.stderr)
        return None

# --- Data Gathering from Kubernetes (Same as before) ---

def get_node_to_cadvisor_map(cadvisor_namespace=CADVISOR_NAMESPACE):
    """Finds cAdvisor pods and maps node name to cAdvisor pod IP."""
    print(f"Fetching cAdvisor pod IPs from namespace '{cadvisor_namespace}'...", file=sys.stderr)
    kubectl_output = run_kubectl_command([
        'get', 'pods', '-n', cadvisor_namespace,
        '--field-selector=status.phase=Running',
        '-o', 'jsonpath={range .items[*]}{.spec.nodeName}{\"\\t\"}{.status.podIP}{\"\\n\"}'
    ], parse_json=False)

    if kubectl_output is None or not kubectl_output.strip():
        print(f"Warning: Failed to get or find running cAdvisor pods in namespace '{cadvisor_namespace}'.", file=sys.stderr)
        return {}

    node_map = {}
    lines = kubectl_output.strip().split('\n')
    for line in lines:
        if not line: continue
        parts = line.split('\t')
        if len(parts) == 2:
            node_name, pod_ip = parts
            if node_name and pod_ip and pod_ip != "<none>":
                node_map[node_name] = pod_ip
    print(f"Found {len(node_map)} cAdvisor pod IPs.", file=sys.stderr)
    return node_map

def get_target_pods_by_node(namespace=OPEN5GS_NAMESPACE):
    """Gets target pods and groups container info by node name."""
    print(f"Fetching '{namespace}' pod data...", file=sys.stderr)
    pod_data = run_kubectl_command(['get', 'pods', '-n', namespace, '-o', 'json'], parse_json=True)

    if not pod_data or 'items' not in pod_data:
        print(f"Warning: Failed to get pod data from namespace '{namespace}'.", file=sys.stderr)
        return {}

    pods_by_node = defaultdict(dict)
    count = 0
    for pod in pod_data['items']:
        pod_name = pod.get('metadata', {}).get('name', 'UnknownPod')
        node_name = pod.get('spec', {}).get('nodeName')
        phase = pod.get('status', {}).get('phase')

        if not node_name or phase != 'Running': continue

        container_statuses = pod.get('status', {}).get('containerStatuses', [])
        for status in container_statuses:
            if status.get('state', {}).get('running') and status.get('containerID'):
                full_container_id = status['containerID']
                container_name = status.get('name')
                match = re.search(r'://([0-9a-f]{64})', full_container_id)
                if match:
                    container_id_64 = match.group(1)
                    pods_by_node[node_name][container_id_64] = {
                        'pod_name': pod_name,
                        'container_name': container_name
                    }
                    count += 1
    print(f"Found {count} running containers in '{namespace}' namespace across {len(pods_by_node)} nodes.", file=sys.stderr)
    return pods_by_node

# --- cAdvisor Querying and Metric Calculation (Same as before) ---

def parse_timestamp_to_ns(timestamp_str):
    """Converts RFC3339Nano string to nanoseconds since epoch, truncating."""
    if not timestamp_str: return None
    try:
        if timestamp_str.endswith('Z'): timestamp_str = timestamp_str[:-1] + '+00:00'
        if '.' in timestamp_str:
            parts = timestamp_str.split('.')
            base = parts[0]
            if '+' in parts[1]: frac, tz_part = parts[1].split('+', 1); tz_part = '+' + tz_part
            elif '-' in parts[1]: frac, tz_part = parts[1].split('-', 1); tz_part = '-' + tz_part
            else: frac = parts[1]; tz_part = '+00:00'
            if len(frac) > 6: frac = frac[:6]
            timestamp_str = f"{base}.{frac}{tz_part}"
        dt = datetime.fromisoformat(timestamp_str)
        return int(dt.timestamp() * 1e9)
    except Exception as e:
        # print(f"ERROR parsing timestamp '{timestamp_str}': {e}", file=sys.stderr)
        return None

def update_and_calculate_metrics_for_node(node_name, cadvisor_ip, containers_on_node, cadvisor_port=CADVISOR_PORT):
    """
    Fetches latest stats, updates raw history, calculates metrics,
    updates API history, and returns count.
    """
    global container_history, api_metric_history
    if not containers_on_node or not cadvisor_ip: return 0

    cadvisor_url = f"http://{cadvisor_ip}:{cadvisor_port}"
    api_endpoint = f"{cadvisor_url}/api/v1.3/subcontainers?recursive=true"

    # Fetch Current Stats
    try:
        response = requests.get(api_endpoint, timeout=10)
        response.raise_for_status()
        cadvisor_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying cAdvisor on Node '{node_name}': {e}", file=sys.stderr)
        return 0
    except json.JSONDecodeError:
        print(f"Error parsing JSON from cAdvisor on Node '{node_name}'.", file=sys.stderr)
        return 0

    # Process Current Stats and Update RAW History
    processed_in_this_cycle = set()
    current_raw_stats = {}

    for container_entry in cadvisor_data:
        stats_list = container_entry.get("stats", [])
        if not stats_list: continue

        container_id_64 = None
        container_id_path = container_entry.get("id")
        if isinstance(container_id_path, str) and len(container_id_path) == 64 and all(c in '0123456789abcdef' for c in container_id_path):
            container_id_64 = container_id_path
        else:
            aliases = container_entry.get("aliases", [])
            containerd_alias = next((alias for alias in aliases if ':cri-containerd:' in alias), None)
            if containerd_alias:
                match = re.search(r':cri-containerd:([0-9a-f]{64})', containerd_alias)
                if match: container_id_64 = match.group(1)

        if container_id_64 and container_id_64 in containers_on_node and container_id_64 not in processed_in_this_cycle:
            latest_stats = stats_list[-1]
            current_raw_stats[container_id_64] = latest_stats
            processed_in_this_cycle.add(container_id_64)

            ts_str = latest_stats.get("timestamp")
            cpu_total_ns = latest_stats.get("cpu", {}).get("usage", {}).get("total")
            ts_ns = parse_timestamp_to_ns(ts_str)

            if ts_ns is not None and cpu_total_ns is not None:
                 with data_lock:
                     container_history[container_id_64].append((ts_ns, cpu_total_ns))

    # Calculate Metrics and Update API History
    processed_count = 0
    current_timestamp_sec = time.time()

    for container_id, pod_info in containers_on_node.items():
        latest_raw_stats_this_cycle = current_raw_stats.get(container_id)
        cpu_mcore = None
        mem_mib = None
        mem_mib_current_reading = None

        # Calculate CPU Rate from raw history
        with data_lock:
            history = container_history.get(container_id)
            history_copy = list(history) if history else []

        if history_copy and len(history_copy) >= 2:
            oldest_valid = None
            newest_valid = None
            for i in range(len(history_copy) - 1, -1, -1):
                 ts, cpu = history_copy[i]
                 if cpu > 0: newest_valid = (ts, cpu); break
            for i in range(len(history_copy)):
                 ts, cpu = history_copy[i]
                 if cpu > 0: oldest_valid = (ts, cpu); break

            if oldest_valid and newest_valid and oldest_valid[0] < newest_valid[0]:
                try:
                    oldest_ts, oldest_cpu = oldest_valid
                    newest_ts, newest_cpu = newest_valid
                    time_delta_ns = newest_ts - oldest_ts
                    cpu_delta_ns = newest_cpu - oldest_cpu

                    if time_delta_ns > 0 and cpu_delta_ns >= 0:
                        cpu_rate_cores = cpu_delta_ns / time_delta_ns
                        cpu_mcore = cpu_rate_cores * 1000
                        if math.isnan(cpu_mcore): cpu_mcore = None
                    # else: cpu_mcore remains None
                except Exception:
                    cpu_mcore = None

        # Calculate Memory from latest raw stats
        if latest_raw_stats_this_cycle:
            memory_stats = latest_raw_stats_this_cycle.get("memory", {})
            memory_working_set_bytes = memory_stats.get("working_set")
            if memory_working_set_bytes is not None:
                mem_mib_current_reading = memory_working_set_bytes / (1024 * 1024)
            else:
                mem_usage_bytes = memory_stats.get("usage")
                if mem_usage_bytes is not None:
                    mem_mib_current_reading = mem_usage_bytes / (1024 * 1024)
            if mem_mib_current_reading is not None and math.isnan(mem_mib_current_reading):
                 mem_mib_current_reading = None

        # Use last known good memory value if current is zero/None
        if mem_mib_current_reading is not None and mem_mib_current_reading > 0.01:
            mem_mib = mem_mib_current_reading
        else:
            mem_mib = None
            with data_lock:
                api_history = api_metric_history.get(container_id)
                if api_history:
                    for i in range(len(api_history) - 1, -1, -1):
                        _, _, prev_mem = api_history[i]
                        if prev_mem is not None and prev_mem > 0.01:
                            mem_mib = prev_mem; break
            if mem_mib is None:
                 mem_mib = mem_mib_current_reading if mem_mib_current_reading is not None else 0.0

        # Store CALCULATED metrics in API history
        with data_lock:
             api_metric_history[container_id].append( (current_timestamp_sec, cpu_mcore, mem_mib) )

        processed_count += 1

    return processed_count


# --- Background Collector Thread ---

def background_collector():
    """Function executed by the background thread to collect metrics."""
    global node_to_cadvisor_ip_map, target_pods_on_nodes_map
    print("Background collector thread started.")

    # --- Fetch Mappings ONCE at Startup ---
    print("Collector: Fetching initial Kubernetes mappings...", file=sys.stderr)
    temp_cadvisor_map = get_node_to_cadvisor_map(CADVISOR_NAMESPACE)
    temp_pods_map = get_target_pods_by_node(OPEN5GS_NAMESPACE)
    with data_lock:
        node_to_cadvisor_ip_map = temp_cadvisor_map
        target_pods_on_nodes_map = temp_pods_map
    print("Collector: Initial mappings fetched.", file=sys.stderr)
    # --- End Initial Fetch ---

    while not stop_event.is_set():
        try:
            start_cycle_time = time.time()

            # --- Collect Metrics using existing maps ---
            with data_lock: # Get copies of maps fetched at startup
                cadvisor_map_copy = node_to_cadvisor_ip_map.copy()
                pods_map_copy = target_pods_on_nodes_map.copy()

            if not pods_map_copy:
                 # Print warning only if map is empty after initial fetch
                 if not target_pods_on_nodes_map: # Check original map
                     print(f"Collector Warning: No running pods found in namespace '{OPEN5GS_NAMESPACE}'.", file=sys.stderr)
                 pass # Continue waiting
            elif not cadvisor_map_copy:
                 # Print warning only if map is empty after initial fetch
                 if not node_to_cadvisor_ip_map: # Check original map
                     print(f"Collector Warning: Could not find running cAdvisor pods in namespace '{CADVISOR_NAMESPACE}'.", file=sys.stderr)
            else:
                nodes_to_process = sorted(pods_map_copy.keys())
                for node_name in nodes_to_process:
                    containers_on_this_node = pods_map_copy.get(node_name, {})
                    cadvisor_pod_ip = cadvisor_map_copy.get(node_name)
                    if cadvisor_pod_ip and containers_on_this_node:
                        # This function updates the global histories
                        update_and_calculate_metrics_for_node(
                            node_name, cadvisor_pod_ip, containers_on_this_node, CADVISOR_PORT
                        )
                    # else: Skip node if no cAdvisor IP found for it in the initial map

            # --- Wait for next cycle ---
            elapsed_time = time.time() - start_cycle_time
            sleep_time = max(0, COLLECTION_INTERVAL_SECONDS - elapsed_time)
            stop_event.wait(sleep_time) # Interruptible sleep

        except Exception as e:
            print(f"\nError in background collector loop: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            stop_event.wait(COLLECTION_INTERVAL_SECONDS) # Wait before retrying

    print("Background collector thread stopped.")


# --- Flask Web Application (Same as before) ---
app = Flask(__name__)

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index_graphs.html', interval=COLLECTION_INTERVAL_SECONDS * 1000)

@app.route('/metrics')
def metrics_api():
    """Provides the latest time-series metrics data as JSON."""
    global node_to_cadvisor_ip_map, target_pods_on_nodes_map, api_metric_history
    response_data = {}

    with data_lock:
        # Use the maps fetched at startup
        pods_map_copy = target_pods_on_nodes_map.copy()
        history_copy = {k: list(v) for k, v in api_metric_history.items()}

    for node_name, containers in pods_map_copy.items():
        node_data = {}
        sorted_container_items = sorted(containers.items(), key=lambda item: item[1]['container_name'])

        for container_id, pod_info in sorted_container_items:
            history_data = history_copy.get(container_id, [])
            if history_data:
                timestamps = [item[0] for item in history_data]
                cpu_values = [item[1] for item in history_data]
                mem_values = [item[2] for item in history_data]

                node_data[container_id] = {
                    "pod_name": pod_info['pod_name'],
                    "container_name": pod_info['container_name'],
                    "timestamps": timestamps,
                    "cpu_mcore": cpu_values,
                    "memory_mib": mem_values
                }
        if node_data:
            response_data[node_name] = node_data

    return jsonify(response_data)

# --- Main Execution (Same as before) ---

if __name__ == "__main__":
    print("Starting background collector thread...")
    collector_thread = threading.Thread(target=background_collector, daemon=True)
    collector_thread.start()

    print(f"Starting Flask web server on http://0.0.0.0:5000 for namespace '{OPEN5GS_NAMESPACE}'...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    print("Flask server stopped. Signaling collector thread to stop...")
    stop_event.set()
    collector_thread.join(timeout=5)
    print("Exiting.")

