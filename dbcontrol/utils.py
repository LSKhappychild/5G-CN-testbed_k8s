#!/usr/bin/env python3

import subprocess

def get_mongodb_ip(namespace="open5gs"):
    """
    Retrieve the IP of the 'open-mongodb' pod running in the given namespace.
    Returns None if no open-mongodb pod is found.
    """
    try:
        # Run the kubectl command and capture its output
        output = subprocess.check_output(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "wide"],
            text=True
        )
    except subprocess.CalledProcessError as e:
        print("Error calling kubectl:", e)
        return None

    lines = output.strip().split("\n")
    if len(lines) < 2:
        # No data returned
        return None
    
    # The first line is the header, e.g. "NAME  READY  STATUS  RESTARTS  AGE  IP  NODE  ..."
    # We'll iterate over the subsequent lines
    for line in lines[1:]:
        columns = line.split()
        if not columns:
            continue
        
        # columns[0] is the Pod name. We look for "open-mongodb-..."
        pod_name = columns[0]
        if pod_name.startswith("open-mongodb"):
            # columns[5] is typically the IP in "kubectl get pods -o wide" output
            pod_ip = columns[5]
            return pod_ip

    return None

if __name__ == "__main__":
    mongodb_ip = get_mongodb_ip(namespace="open5gs")
    if mongodb_ip:
        print(f"MongoDB Pod IP: {mongodb_ip}")
    else:
        print("Could not find an open-mongodb pod in namespace 'open5gs'.")
