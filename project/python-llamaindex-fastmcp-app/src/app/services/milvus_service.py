from pymilvus import Milvus, DataType

class MilvusService:
    def __init__(self, host: str, port: str):
        self.client = Milvus(host=host, port=port)

    def create_collection(self, collection_name: str, fields: list):
        collection_param = {
            "collection_name": collection_name,
            "fields": fields
        }
        self.client.create_collection(collection_param)

    def insert_data(self, collection_name: str, records: list):
        self.client.insert(collection_name=collection_name, records=records)

    def search(self, collection_name: str, query_vectors: list, top_k: int):
        search_param = {
            "collection_name": collection_name,
            "query_records": query_vectors,
            "top_k": top_k
        }
        return self.client.search(**search_param)

    def get_collection_info(self, collection_name: str):
        return self.client.get_collection_info(collection_name)

    def drop_collection(self, collection_name: str):
        self.client.drop_collection(collection_name)