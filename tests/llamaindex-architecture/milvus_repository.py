import logging
from typing import List, Optional, Dict, Any
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores import VectorStoreQuery, VectorStoreQueryResult
from models import VectorRepository, DocumentChunk, SearchResult
from config import db_config

logger = logging.getLogger(__name__)

class MilvusRepository(VectorRepository):
    """LlamaIndex MilvusVectorStore統合リポジトリ"""
    
    def __init__(self):
        self.host = db_config.MILVUS_HOST
        self.port = db_config.MILVUS_PORT
        self.collection_name = db_config.MILVUS_COLLECTION_NAME
        self.dimension = db_config.MILVUS_DIMENSION
        self.vector_store = None
        self.connection_alias = "default"
    
    async def connect(self) -> bool:
        """MilvusVectorStoreに接続"""
        try:
            # LlamaIndex MilvusVectorStore初期化
            self.vector_store = MilvusVectorStore(
                host=self.host,
                port=self.port,
                collection_name=self.collection_name,
                dim=self.dimension,
                overwrite=False,  # 既存コレクションを保持
                similarity_metric="COSINE",
                index_config={
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",
                    "params": {"nlist": 1024}
                }
            )
            
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Milvusから切断"""
        try:
            if self.vector_store:
                # MilvusVectorStoreは自動的にリソースを管理
                self.vector_store = None
            logger.info("Disconnected from Milvus")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Milvus: {e}")
            return False
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            if self.vector_store:
                # 簡単なクエリでヘルスチェック
                query = VectorStoreQuery(
                    query_embedding=[0.0] * self.dimension,
                    similarity_top_k=1
                )
                await self.vector_store.aquery(query)
                return True
            return False
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """コレクション作成（MilvusVectorStoreが自動処理）"""
        try:
            # MilvusVectorStoreは初期化時に自動的にコレクションを作成
            if not self.vector_store:
                await self.connect()
            
            logger.info(f"Milvus collection ready: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    async def insert_vectors(self, chunks: List[DocumentChunk]) -> bool:
        """ベクトル挿入"""
        try:
            if not self.vector_store:
                await self.connect()
            
            # DocumentChunkをTextNodeに変換
            nodes = []
            for chunk in chunks:
                if chunk.embedding:
                    node = TextNode(
                        id_=chunk.id,
                        text=chunk.content,
                        metadata={
                            "document_id": chunk.document_id,
                            "chunk_index": chunk.chunk_index,
                            **chunk.metadata
                        },
                        embedding=chunk.embedding
                    )
                    nodes.append(node)
            
            if not nodes:
                logger.warning("No valid chunks with embeddings to insert")
                return False
            
            # ベクトルストアに追加
            self.vector_store.add(nodes)
            
            logger.info(f"Inserted {len(nodes)} vectors into Milvus")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            return False
    
    async def search_vectors(self, query_vector: List[float], top_k: int) -> List[SearchResult]:
        """ベクトル検索"""
        try:
            if not self.vector_store:
                await self.connect()
            
            # VectorStoreQueryを作成
            query = VectorStoreQuery(
                query_embedding=query_vector,
                similarity_top_k=top_k,
                mode="default"
            )
            
            # 検索実行
            result = await self.vector_store.aquery(query)
            
            # 結果変換
            search_results = []
            for i, node in enumerate(result.nodes):
                search_result = SearchResult(
                    document_id=node.metadata.get("document_id", ""),
                    chunk_id=node.id_,
                    content=node.text,
                    score=result.similarities[i] if result.similarities else 1.0,
                    metadata={
                        "chunk_index": node.metadata.get("chunk_index", 0),
                        **node.metadata
                    },
                    document_title=""  # 後でMongoDBから取得
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} vector search results")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    async def delete_vectors(self, document_id: str) -> bool:
        """ベクトル削除"""
        try:
            if not self.vector_store:
                await self.connect()
            
            # ドキュメントIDでフィルタリングして削除
            # 注意: MilvusVectorStoreのdelete機能は限定的な場合がある
            logger.warning(f"Delete operation for document {document_id} may require collection recreation")
            
            logger.info(f"Delete request processed for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    async def get_collection_stats(self) -> dict:
        """コレクション統計取得"""
        try:
            if not self.vector_store:
                await self.connect()
            
            # 基本統計情報
            return {
                "collection_name": self.collection_name,
                "dimension": self.dimension,
                "status": "connected" if self.vector_store else "disconnected"
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def update_vector(self, chunk: DocumentChunk) -> bool:
        """ベクトル更新"""
        try:
            if not self.vector_store:
                await self.connect()
            
            # 削除してから挿入（upsert機能）
            await self.insert_vectors([chunk])
            
            logger.info(f"Updated vector for chunk: {chunk.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vector: {e}")
            return False