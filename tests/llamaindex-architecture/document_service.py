import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
from pathlib import Path
import hashlib

from llama_index.core import Document as LIDocument
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.readers import SimpleDirectoryReader

from models import Document, DocumentChunk, SearchResult, DocumentRelation
from ollama_client import ollama_client
from milvus_repository import MilvusRepository
from mongo_repository import MongoRepository
from neo4j_repository import Neo4jRepository
from redis_repository import RedisRepository
from config import db_config, sys_config

logger = logging.getLogger(__name__)

class DocumentService:
    """ドキュメント統合サービス"""
    
    def __init__(self):
        # リポジトリ初期化
        self.milvus_repo = MilvusRepository()
        self.mongo_repo = MongoRepository()
        self.neo4j_repo = Neo4jRepository()
        self.redis_repo = RedisRepository()
        
        # LlamaIndexコンポーネント
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=db_config.CHUNK_SIZE,
            chunk_overlap=db_config.CHUNK_OVERLAP
        )
        
        self.initialized = False
    
    async def initialize(self) -> bool:
        """サービス初期化"""
        try:
            # 各リポジトリの接続
            tasks = [
                self.milvus_repo.connect(),
                self.mongo_repo.connect(),
                self.neo4j_repo.connect(),
                self.redis_repo.connect(),
                ollama_client.initialize()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果確認
            failed_services = []
            service_names = ["Milvus", "MongoDB", "Neo4j", "Redis", "Ollama"]
            
            for i, result in enumerate(results):
                if isinstance(result, Exception) or not result:
                    failed_services.append(service_names[i])
                    logger.error(f"Failed to initialize {service_names[i]}: {result}")
            
            if failed_services:
                logger.error(f"Failed to initialize services: {failed_services}")
                return False
            
            self.initialized = True
            logger.info("Document service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize document service: {e}")
            return False
    
    async def shutdown(self):
        """サービスシャットダウン"""
        try:
            tasks = [
                self.milvus_repo.disconnect(),
                self.mongo_repo.disconnect(),
                self.neo4j_repo.disconnect(),
                self.redis_repo.disconnect()
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("Document service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def process_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """ファイル処理とドキュメント保存"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # ファイル読み込み
            documents = await self._load_file(file_path)
            if not documents:
                logger.error(f"Failed to load file: {file_path}")
                return None
            
            document = documents[0]  # 通常は1つのファイルから1つのドキュメント
            
            # メタデータ設定
            if metadata:
                document.metadata.update(metadata)
            
            # ドキュメント保存
            document_id = await self._save_document(document)
            if not document_id:
                logger.error(f"Failed to save document: {file_path}")
                return None
            
            # チャンク化とベクトル化
            await self._process_chunks(document)
            
            # グラフノード作成
            await self.neo4j_repo.create_document_node(document)
            
            # 関係性分析と作成
            await self._analyze_and_create_relations(document)
            
            logger.info(f"Successfully processed file: {file_path}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return None
    
    async def _load_file(self, file_path: str) -> List[Document]:
        """ファイル読み込み"""
        try:
            # ファイル存在確認
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # ファイルサイズ確認
            file_size = os.path.getsize(file_path)
            if file_size > sys_config.MAX_FILE_SIZE:
                raise ValueError(f"File too large: {file_size} bytes")
            
            # ファイル拡張子確認
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in sys_config.SUPPORTED_FILE_TYPES:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # LlamaIndexでファイル読み込み
            reader = SimpleDirectoryReader(input_files=[file_path])
            li_documents = reader.load_data()
            
            # Document形式に変換
            documents = []
            for li_doc in li_documents:
                # ファイルハッシュ生成
                file_hash = self._generate_file_hash(file_path)
                
                document = Document(
                    id=file_hash,
                    title=os.path.basename(file_path),
                    content=li_doc.text,
                    file_path=file_path,
                    file_type=file_ext,
                    metadata={
                        "file_size": file_size,
                        "file_hash": file_hash,
                        **li_doc.metadata
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                documents.append(document)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")
            return []
    
    def _generate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュ生成"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def _save_document(self, document: Document) -> str:
        """ドキュメント保存"""
        try:
            # MongoDB保存
            document_id = await self.mongo_repo.save_document(document)
            
            # キーワード抽出とタグ設定
            keywords = await ollama_client.extract_keywords(document.content)
            if keywords:
                document.tags = keywords
                await self.mongo_repo.update_document(document)
            
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return ""
    
    async def _process_chunks(self, document: Document):
        """チャンク処理"""
        try:
            # LlamaIndexドキュメント作成
            li_document = LIDocument(text=document.content, doc_id=document.id)
            
            # チャンク化
            nodes = self.node_parser.get_nodes_from_documents([li_document])
            
            # DocumentChunk作成とエンベディング生成
            chunks = []
            for i, node in enumerate(nodes):
                # エンベディング生成
                embedding = await ollama_client.generate_embedding(node.text)
                
                chunk = DocumentChunk(
                    id=f"{document.id}_chunk_{i}",
                    document_id=document.id,
                    content=node.text,
                    chunk_index=i,
                    metadata={
                        "start_char_idx": node.start_char_idx,
                        "end_char_idx": node.end_char_idx
                    },
                    embedding=embedding
                )
                chunks.append(chunk)
            
            # Milvusに保存
            if chunks:
                await self.milvus_repo.insert_vectors(chunks)
            
            logger.info(f"Processed {len(chunks)} chunks for document {document.id}")
            
        except Exception as e:
            logger.error(f"Failed to process chunks: {e}")
    
    async def _analyze_and_create_relations(self, document: Document):
        """関係性分析と作成"""
        try:
            # 既存ドキュメントとの関係性分析
            existing_docs = await self.mongo_repo.search_documents({"limit": 50})
            
            for existing_doc in existing_docs:
                if existing_doc.id == document.id:
                    continue
                
                # 関係性分析
                relation_info = await ollama_client.analyze_document_relations(
                    document.content[:1000],  # 最初の1000文字
                    existing_doc.content[:1000]
                )
                
                if relation_info and relation_info["strength"] > sys_config.SIMILARITY_THRESHOLD:
                    # 関係作成
                    relation = DocumentRelation(
                        source_doc_id=document.id,
                        target_doc_id=existing_doc.id,
                        relation_type=relation_info["relation_type"],
                        strength=relation_info["strength"],
                        metadata={"reason": relation_info["reason"]}
                    )
                    
                    await self.neo4j_repo.create_relation(relation)
            
        except Exception as e:
            logger.error(f"Failed to analyze relations: {e}")
    
    async def search_documents(
        self, 
        query: str, 
        search_type: str = "hybrid",
        filters: Dict[str, Any] = None,
        limit: int = None
    ) -> List[SearchResult]:
        """ドキュメント検索"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if limit is None:
                limit = sys_config.VECTOR_SEARCH_TOP_K
            
            # キャッシュキー生成
            cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}:{search_type}:{limit}"
            
            # キャッシュ確認
            cached_results = await self.redis_repo.get(cache_key)
            if cached_results:
                logger.info("Returning cached search results")
                return cached_results
            
            results = []
            
            if search_type in ["vector", "hybrid"]:
                # ベクトル検索
                vector_results = await self._vector_search(query, limit)
                results.extend(vector_results)
            
            if search_type in ["text", "hybrid"]:
                # テキスト検索
                text_results = await self._text_search(query, filters, limit)
                results.extend(text_results)
            
            # 重複除去とスコア統合
            results = await self._merge_search_results(results)
            
            # 結果をキャッシュ
            await self.redis_repo.set(cache_key, results, expire_time=300)  # 5分
            
            logger.info(f"Found {len(results)} search results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    async def _vector_search(self, query: str, limit: int) -> List[SearchResult]:
        """ベクトル検索"""
        try:
            # クエリのエンベディング生成
            query_embedding = await ollama_client.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Milvus検索
            results = await self.milvus_repo.search_vectors(query_embedding, limit)
            
            # ドキュメントタイトル補完
            for result in results:
                document = await self.mongo_repo.get_document(result.document_id)
                if document:
                    result.document_title = document.title
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform vector search: {e}")
            return []
    
    async def _text_search(self, query: str, filters: Dict[str, Any], limit: int) -> List[SearchResult]:
        """テキスト検索"""
        try:
            search_query = {"text": query, "limit": limit}
            if filters:
                search_query.update(filters)
            
            documents = await self.mongo_repo.search_documents(search_query)
            
            # SearchResult形式に変換
            results = []
            for doc in documents:
                result = SearchResult(
                    document_id=doc.id,
                    chunk_id=f"{doc.id}_full",
                    content=doc.content[:500],  # 最初の500文字
                    score=1.0,  # テキスト検索はスコア1.0
                    metadata=doc.metadata,
                    document_title=doc.title
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform text search: {e}")
            return []
    
    async def _merge_search_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """検索結果マージ"""
        try:
            # ドキュメントIDでグループ化
            doc_results = {}
            for result in results:
                if result.document_id not in doc_results:
                    doc_results[result.document_id] = []
                doc_results[result.document_id].append(result)
            
            # 各ドキュメントの最高スコアを採用
            merged_results = []
            for doc_id, doc_result_list in doc_results.items():
                best_result = max(doc_result_list, key=lambda x: x.score)
                merged_results.append(best_result)
            
            # スコア順ソート
            merged_results.sort(key=lambda x: x.score, reverse=True)
            
            return merged_results[:sys_config.RERANK_TOP_K]
            
        except Exception as e:
            logger.error(f"Failed to merge search results: {e}")
            return results
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """ドキュメント取得"""
        try:
            # キャッシュ確認
            cache_key = f"doc:{document_id}"
            cached_doc = await self.redis_repo.get(cache_key)
            if cached_doc:
                return Document(**cached_doc)
            
            # MongoDB取得
            document = await self.mongo_repo.get_document(document_id)
            if document:
                # キャッシュ保存
                doc_dict = {
                    "id": document.id,
                    "title": document.title,
                    "content": document.content,
                    "file_path": document.file_path,
                    "file_type": document.file_type,
                    "metadata": document.metadata,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat(),
                    "tags": document.tags
                }
                await self.redis_repo.set(cache_key, doc_dict)
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    async def delete_document(self, document_id: str) -> bool:
        """ドキュメント削除"""
        try:
            # 各データベースから削除
            tasks = [
                self.mongo_repo.delete_document(document_id),
                self.milvus_repo.delete_vectors(document_id),
                self.neo4j_repo.delete_document_node(document_id),
                self.redis_repo.delete(f"doc:{document_id}")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 削除結果確認
            success = all(result is True or not isinstance(result, Exception) for result in results)
            
            if success:
                logger.info(f"Successfully deleted document: {document_id}")
            else:
                logger.error(f"Failed to delete document completely: {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def get_related_documents(self, document_id: str) -> List[str]:
        """関連ドキュメント取得"""
        try:
            return await self.neo4j_repo.find_related_documents(document_id)
        except Exception as e:
            logger.error(f"Failed to get related documents: {e}")
            return []
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """システム統計取得"""
        try:
            tasks = [
                self.mongo_repo.get_collection_stats(),
                self.milvus_repo.get_collection_stats(),
                self.neo4j_repo.get_graph_stats(),
                self.redis_repo.get_cache_stats()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "mongodb": results[0] if not isinstance(results[0], Exception) else {},
                "milvus": results[1] if not isinstance(results[1], Exception) else {},
                "neo4j": results[2] if not isinstance(results[2], Exception) else {},
                "redis": results[3] if not isinstance(results[3], Exception) else {}
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}