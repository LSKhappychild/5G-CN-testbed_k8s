#!/usr/bin/env python3

from pymongo import MongoClient

def main():
    # Replace this IP and port with the actual Pod IP if it changes
    mongo_uri = "mongodb://10.244.4.68:27017"

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client["open5gs"]

    # The Open5GS subscribers are generally in the 'subscribers' collection
    subscribers_collection = db["subscribers"]

    # Query all documents (subscribers)
    subscribers = subscribers_collection.find()

    # Print them
    for subscriber in subscribers:
        print(subscriber)

if __name__ == "__main__":
    main()

