from pymilvus import connections, Collection, DataType, FieldSchema, CollectionSchema
from typing import List, Dict, Any, Optional
import numpy as np


class MilvusClient:
    """Milvusを使用したベクトル検索クラス"""
    
    def __init__(self, host: str = "localhost", port: str = "19530", collection_name: str = "document_vectors"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        self.connect()
        
    def connect(self):
        """Milvusサーバーに接続"""
        connections.connect("default", host=self.host, port=self.port)
        
    def create_collection(self, dimension: int = 768):
        """コレクションを作成"""
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
        ]
        
        schema = CollectionSchema(fields, "RAGシステム用ドキュメントベクトル")
        
        if self.collection_name in [c.name for c in connections.get_connection().list_collections()]:
            self.collection = Collection(self.collection_name)
        else:
            self.collection = Collection(self.collection_name, schema)
            
        # インデックス作成
        index_params = {
            "metric_type": "IP",  # Inner Product
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index("embedding", index_params)
        
    def insert_vectors(self, document_id: str, chunk_texts: List[str], embeddings: List[List[float]]):
        """ベクトルを挿入"""
        if not self.collection:
            raise ValueError("コレクションが初期化されていません")
            
        data = []
        for i, (text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            data.append([
                f"{document_id}_{i}",  # chunk_id
                document_id,
                embedding,
                text
            ])
            
        # データ形式を調整
        formatted_data = [
            [item[1] for item in data],  # document_id
            [item[0] for item in data],  # chunk_id  
            [item[2] for item in data],  # embedding
            [item[3] for item in data]   # text
        ]
        
        self.collection.insert(formatted_data)
        self.collection.flush()
        
    def search_similar(self, query_embedding: List[float], top_k: int = 5, 
                      document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """類似ベクトル検索"""
        if not self.collection:
            raise ValueError("コレクションが初期化されていません")
            
        self.collection.load()
        
        search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
        
        # フィルター条件
        expr = None
        if document_filter:
            expr = f'document_id == "{document_filter}"'
            
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["document_id", "chunk_id", "text"]
        )
        
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "document_id": hit.entity.get("document_id"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "text": hit.entity.get("text"),
                    "score": hit.score
                })
                
        return formatted_results
        
    def delete_document_vectors(self, document_id: str):
        """指定ドキュメントのベクトルを削除"""
        if not self.collection:
            raise ValueError("コレクションが初期化されていません")
            
        expr = f'document_id == "{document_id}"'
        self.collection.delete(expr)
        
    def get_collection_stats(self) -> Dict[str, Any]:
        """コレクションの統計情報を取得"""
        if not self.collection:
            return {}
            
        self.collection.load()
        return {
            "num_entities": self.collection.num_entities,
            "description": self.collection.description
        }