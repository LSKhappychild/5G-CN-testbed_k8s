#!/usr/bin/env python3
from pymongo import MongoClient

def main():
    # Update this URI to match your actual MongoDB endpoint
    mongo_uri = "mongodb://10.244.4.63:27017"
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client["open5gs"]
    subscribers_collection = db["subscribers"]

    # Delete all documents (subscribers) in the 'subscribers' collection
    result = subscribers_collection.delete_many({})
    
    print(f"Deleted {result.deleted_count} subscribers from the database.")

if __name__ == "__main__":
    main()
