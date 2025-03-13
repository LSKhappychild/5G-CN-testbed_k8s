#!/usr/bin/env python3
import argparse
import sys

from ruamel.yaml import YAML
from pymongo import MongoClient

def feed_subscribers_minimal(yaml_file, mongo_uri):
    """
    Reads subscribers from a YAML file and inserts them directly into
    the 'open5gs.subscribers' MongoDB collection. No checks or skipping logic.
    """
    yaml = YAML()
    try:
        with open(yaml_file, "r") as f:
            all_subscribers = yaml.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {yaml_file}: {e}")
        sys.exit(1)

    # all_subscribers should be a dictionary, e.g.:
    # {
    #   "subscriber_1": { ... },
    #   "subscriber_2": { ... },
    #   ...
    # }
    if not all_subscribers or not isinstance(all_subscribers, dict):
        print(f"[ERROR] {yaml_file} did not load a valid top-level dict.")
        sys.exit(1)

    # Connect to MongoDB
    try:
        client = MongoClient(mongo_uri)
        db = client["open5gs"]
        subscribers_col = db["subscribers"]
    except Exception as e:
        print(f"[ERROR] MongoDB connection issue: {e}")
        sys.exit(1)

    before_count = subscribers_col.count_documents({})
    print(f"[INFO] Documents before insertion: {before_count}")

    # Convert dictionary-of-subscribers to list-of-subscriber-docs
    subscriber_docs = list(all_subscribers.values())

    # Remove _id if present, so Mongo can assign new object IDs
    for doc in subscriber_docs:
        if "_id" in doc:
            doc.pop("_id", None)

    try:
        result = subscribers_col.insert_many(subscriber_docs, ordered=False)
        inserted_count = len(result.inserted_ids)
        print(f"[INFO] Inserted {inserted_count} documents.")
    except Exception as e:
        print(f"[ERROR] Insert error: {e}")
        sys.exit(1)

    after_count = subscribers_col.count_documents({})
    print(f"[INFO] Documents after insertion: {after_count}")

def main():
    parser = argparse.ArgumentParser(
        description="Minimal feeder script: reads all YAML entries and inserts them into open5gs.subscribers."
    )
    parser.add_argument("--yaml-file", default="subscribers.yaml",
                        help="Path to the YAML file to insert.")
    parser.add_argument("--mongo-uri", default="mongodb://10.244.4.63:27017",
                        help="MongoDB URI (with host:port, or auth if needed).")
    args = parser.parse_args()

    feed_subscribers_minimal(args.yaml_file, args.mongo_uri)

if __name__ == "__main__":
    main()
