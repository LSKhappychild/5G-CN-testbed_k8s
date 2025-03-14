#!/usr/bin/env python3
from pymongo import MongoClient
from utils import get_mongodb_ip
def main():
    # Update this URI to match your actual MongoDB endpoint
    mongodb_ip = get_mongodb_ip(namespace="open5gs")
    
    mongo_uri = f"mongodb://{mongodb_ip}:27017"
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client["open5gs"]
    subscribers_collection = db["subscribers"]

    # Delete all documents (subscribers) in the 'subscribers' collection
    result = subscribers_collection.delete_many({})
    
    print(f"Deleted {result.deleted_count} subscribers from the database.")

if __name__ == "__main__":
    main()
