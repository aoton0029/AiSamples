from pymongo import MongoClient
import os

class MongoDBService:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_HOST'), int(os.getenv('MONGODB_PORT')))
        self.db = self.client[os.getenv('MONGODB_DATABASE')]
    
    def create_document(self, collection_name, document):
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def read_document(self, collection_name, query):
        collection = self.db[collection_name]
        document = collection.find_one(query)
        return document

    def update_document(self, collection_name, query, update_values):
        collection = self.db[collection_name]
        result = collection.update_one(query, {'$set': update_values})
        return result.modified_count

    def delete_document(self, collection_name, query):
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count

    def list_documents(self, collection_name):
        collection = self.db[collection_name]
        return list(collection.find())