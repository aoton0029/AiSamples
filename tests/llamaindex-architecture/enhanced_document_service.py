import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
from pathlib import Path
import hashlib

from llama_index.core import VectorStoreIndex, Document as LIDocument, StorageContext
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.query_engine import VectorStoreQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor, KeywordNodePostprocessor
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.schema import BaseNode, TextNode

from models import Document, DocumentChunk, SearchResult, DocumentRelation
from ollama_client import ollama_client
from milvus_repository import MilvusRepository
from mongo_repository import MongoRepository
from enhanced_neo4j_repository import EnhancedNeo4jRepository
from redis_repository import RedisRepository
from config import db_config, sys_config

logger = logging.getLogger(__name__)

class EnhancedDocumentService:
    """LlamaIndex統合強化ドキュメントサービス"""
    
    def __init__(self):
        # リポジトリ初期化
        self.milvus_repo = MilvusRepository()
        self.mongo_repo = MongoRepository()
        self.neo4j_repo = EnhancedNeo4jRepository()
        self.redis_repo = RedisRepository()
        
        # LlamaIndex コンポーネント
        self.node_parser = SentenceSplitter(
            chunk_size=db_config.CHUNK_SIZE,
            chunk_overlap=db_config.CHUNK_OVERLAP,
            separator=" "
        )
        
        # インデックスとクエリエンジン
        self.vector_index = None
        self.query_engine = None
        self.retriever = None
        
        self.initialized = False
    
    async def initialize(self) -> bool:
        """拡張サービス初期化"""
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
            
            # LlamaIndexコンポーネント初期化
            await self._initialize_llamaindex_components()
            
            # モデルウォームアップ
            await ollama_client.warm_up_models()
            
            self.initialized = True
            logger.info("Enhanced document service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced document service: {e}")
            return False
    
    async def _initialize_llamaindex_components(self):
        """LlamaIndexコンポーネント初期化"""
        try:
            # ストレージコンテキスト作成
            storage_context = StorageContext.from_defaults(
                vector_store=self.milvus_repo.vector_store
            )
            
            # ベクトルインデックス作成/読み込み
            try:
                self.vector_index = VectorStoreIndex.from_vector_store(
                    vector_store=self.milvus_repo.vector_store,
                    embed_model=ollama_client.embedding_client
                )
            except Exception:
                # 新規作成
                self.vector_index = VectorStoreIndex(
                    nodes=[],
                    storage_context=storage_context,
                    embed_model=ollama_client.embedding_client
                )
            
            # リトリーバー作成
            self.retriever = VectorIndexRetriever(
                index=self.vector_index,
                similarity_top_k=sys_config.VECTOR_SEARCH_TOP_K
            )
            
            # クエリエンジン作成
            self.query_engine = VectorStoreQueryEngine(
                retriever=self.retriever,
                response_synthesizer=None,  # カスタム合成
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=sys_config.SIMILARITY_THRESHOLD),
                    KeywordNodePostprocessor(exclude_keywords=["irrelevant"])
                ]
            )
            
            logger.info("LlamaIndex components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize LlamaIndex components: {e}")
    
    async def process_file_enhanced(
        self, 
        file_path: str, 
        metadata: Dict[str, Any] = None,
        extract_entities: bool = True,
        analyze_sentiment: bool = True
    ) -> Optional[str]:
        """拡張ファイル処理"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # ファイル読み込み
            documents = await self._load_file(file_path)
            if not documents:
                logger.error(f"Failed to load file: {file_path}")
                return None
            
            document = documents[0]
            
            # メタデータ設定
            if metadata:
                document.metadata.update(metadata)
            
            # 拡張メタデータ生成
            enhanced_metadata = await self._generate_enhanced_metadata(
                document, extract_entities, analyze_sentiment
            )
            document.metadata.update(enhanced_metadata)
            
            # ドキュメント保存
            document_id = await self._save_document(document)
            if not document_id:
                logger.error(f"Failed to save document: {file_path}")
                return None
            
            # 拡張チャンク処理
            await self._process_chunks_enhanced(document)
            
            # 拡張グラフノード作成
            await self.neo4j_repo.create_document_node(document)
            
            # 関係性分析と作成
            await self._analyze_and_create_relations_enhanced(document)
            
            logger.info(f"Successfully processed file with enhancements: {file_path}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return None
    
    async def _generate_enhanced_metadata(
        self, 
        document: Document, 
        extract_entities: bool, 
        analyze_sentiment: bool
    ) -> Dict[str, Any]:
        """拡張メタデータ生成"""
        try:
            enhanced_metadata = {}
            
            # 感情分析
            if analyze_sentiment:
                sentiment = await ollama_client.analyze_sentiment(document.content[:1000])
                enhanced_metadata["sentiment"] = sentiment
            
            # エンティティ抽出
            if extract_entities:
                entities = await ollama_client.extract_entities(document.content[:2000])
                enhanced_metadata["entities"] = entities
            
            # キーワード抽出
            keywords = await ollama_client.extract_keywords(document.content, max_keywords=15)
            if keywords:
                document.tags = keywords
                enhanced_metadata["auto_keywords"] = keywords
            
            # 文書統計
            enhanced_metadata["statistics"] = {
                "word_count": len(document.content.split()),
                "char_count": len(document.content),
                "paragraph_count": len(document.content.split('\n\n'))
            }
            
            return enhanced_metadata
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced metadata: {e}")
            return {}
    
    async def _process_chunks_enhanced(self, document: Document):
        """拡張チャンク処理"""
        try:
            # LlamaIndexドキュメント作成
            li_document = LIDocument(
                text=document.content, 
                doc_id=document.id,
                metadata=document.metadata
            )
            
            # チャンク化（拡張パーサー使用）
            nodes = self.node_parser.get_nodes_from_documents([li_document])
            
            # エンベディング生成（バッチ処理）
            texts = [node.text for node in nodes]
            embeddings = await ollama_client.generate_embeddings_batch(texts, batch_size=5)
            
            # DocumentChunk作成
            chunks = []
            enhanced_nodes = []
            
            for i, (node, embedding) in enumerate(zip(nodes, embeddings)):
                if embedding:
                    # チャンクメタデータ強化
                    chunk_metadata = {
                        "start_char_idx": node.start_char_idx,
                        "end_char_idx": node.end_char_idx,
                        "chunk_length": len(node.text),
                        "word_count": len(node.text.split()),
                        **node.metadata
                    }
                    
                    chunk = DocumentChunk(
                        id=f"{document.id}_chunk_{i}",
                        document_id=document.id,
                        content=node.text,
                        chunk_index=i,
                        metadata=chunk_metadata,
                        embedding=embedding
                    )
                    chunks.append(chunk)
                    
                    # TextNode作成（LlamaIndex用）
                    enhanced_node = TextNode(
                        id_=chunk.id,
                        text=node.text,
                        metadata=chunk_metadata,
                        embedding=embedding
                    )
                    enhanced_nodes.append(enhanced_node)
            
            # Milvusに保存
            if chunks:
                await self.milvus_repo.insert_vectors(chunks)
            
            # ベクトルインデックス更新
            if enhanced_nodes and self.vector_index:
                self.vector_index.insert_nodes(enhanced_nodes)
            
            logger.info(f"Processed {len(chunks)} enhanced chunks for document {document.id}")
            
        except Exception as e:
            logger.error(f"Failed to process enhanced chunks: {e}")
    
    async def intelligent_search(
        self, 
        query: str, 
        search_type: str = "hybrid",
        include_metadata: bool = True,
        rerank: bool = True,
        limit: int = None
    ) -> List[SearchResult]:
        """知的検索機能"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if limit is None:
                limit = sys_config.VECTOR_SEARCH_TOP_K
            
            # キャッシュキー生成
            cache_key = f"intelligent_search:{hashlib.md5(query.encode()).hexdigest()}:{search_type}:{include_metadata}:{rerank}:{limit}"
            
            # キャッシュ確認
            cached_results = await self.redis_repo.get(cache_key)
            if cached_results:
                logger.info("Returning cached intelligent search results")
                return cached_results
            
            results = []
            
            # LlamaIndexクエリエンジン使用
            if search_type in ["vector", "hybrid"] and self.query_engine:
                vector_results = await self._llamaindex_search(query, limit)
                results.extend(vector_results)
            
            # 従来の検索も並行実行
            if search_type in ["text", "hybrid"]:
                text_results = await self._text_search(query, {}, limit)
                results.extend(text_results)
            
            # 重複除去とマージ
            results = await self._merge_search_results(results)
            
            # リランキング
            if rerank and len(results) > 1:
                results = await self._rerank_results(query, results)
            
            # メタデータ強化
            if include_metadata:
                results = await self._enhance_search_results_metadata(results)
            
            # 結果をキャッシュ
            await self.redis_repo.set(cache_key, results, expire_time=300)
            
            logger.info(f"Found {len(results)} intelligent search results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform intelligent search: {e}")
            return []
    
    async def _llamaindex_search(self, query: str, limit: int) -> List[SearchResult]:
        """LlamaIndexクエリエンジン検索"""
        try:
            # クエリ実行
            response = await self.query_engine.aquery(query)
            
            # 結果変換
            results = []
            for node in response.source_nodes:
                result = SearchResult(
                    document_id=node.node.metadata.get("document_id", ""),
                    chunk_id=node.node.id_,
                    content=node.node.text,
                    score=node.score if hasattr(node, 'score') else 1.0,
                    metadata=node.node.metadata,
                    document_title=""
                )
                results.append(result)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to perform LlamaIndex search: {e}")
            return []
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """結果リランキング"""
        try:
            # クエリエンベディング生成
            query_embedding = await ollama_client.generate_embedding(query)
            if not query_embedding:
                return results
            
            # 各結果のスコア再計算
            reranked_results = []
            for result in results:
                # コンテンツエンベディング生成
                content_embedding = await ollama_client.generate_embedding(result.content)
                if content_embedding:
                    # コサイン類似度計算
                    import numpy as np
                    similarity = np.dot(query_embedding, content_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(content_embedding)
                    )
                    result.score = float(similarity)
                
                reranked_results.append(result)
            
            # スコア順ソート
            reranked_results.sort(key=lambda x: x.score, reverse=True)
            return reranked_results[:sys_config.RERANK_TOP_K]
            
        except Exception as e:
            logger.error(f"Failed to rerank results: {e}")
            return results
    
    async def _enhance_search_results_metadata(self, results: List[SearchResult]) -> List[SearchResult]:
        """検索結果メタデータ強化"""
        try:
            # ドキュメント情報取得
            doc_ids = list(set([result.document_id for result in results]))
            documents = await self.mongo_repo.get_documents_by_ids(doc_ids)
            doc_dict = {doc.id: doc for doc in documents}
            
            # 結果強化
            for result in results:
                if result.document_id in doc_dict:
                    doc = doc_dict[result.document_id]
                    result.document_title = doc.title
                    
                    # メタデータ追加
                    result.metadata.update({
                        "document_file_type": doc.file_type,
                        "document_tags": doc.tags,
                        "document_created_at": doc.created_at.isoformat()
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to enhance search results metadata: {e}")
            return results
    
    async def search_by_prompt(
        self, 
        prompt: str, 
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        include_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """プロンプトベースの類似ドキュメント検索"""
        try:
            logger.info(f"Searching documents by prompt: {prompt}")
            
            # 1. プロンプトのエンベディング生成
            prompt_embedding = await ollama_client.generate_embedding(prompt)
            if not prompt_embedding:
                logger.error("Failed to generate prompt embedding")
                return []
            
            # 2. ベクトル検索実行
            vector_results = await self.milvus_repo.search_vectors(prompt_embedding, max_results * 2)
            
            # 3. 類似度フィルタリング
            filtered_results = [
                result for result in vector_results 
                if result.score >= similarity_threshold
            ]
            
            # 4. ドキュメント詳細情報取得
            doc_ids = list(set([result.document_id for result in filtered_results]))
            documents = await self.mongo_repo.get_documents_by_ids(doc_ids)
            doc_dict = {doc.id: doc for doc in documents}
            
            # 5. 結果構築
            search_results = []
            for result in filtered_results[:max_results]:
                if result.document_id in doc_dict:
                    doc = doc_dict[result.document_id]
                    
                    result_dict = {
                        "document_id": result.document_id,
                        "title": doc.title,
                        "content_snippet": result.content,
                        "file_type": doc.file_type,
                        "file_path": doc.file_path,
                        "tags": doc.tags,
                        "created_at": doc.created_at.isoformat(),
                        "metadata": doc.metadata
                    }
                    
                    if include_scores:
                        result_dict["similarity_score"] = result.score
                    
                    search_results.append(result_dict)
            
            logger.info(f"Found {len(search_results)} documents matching prompt")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search by prompt: {e}")
            return []
    
    async def find_similar_documents_advanced(
        self,
        reference_text: str,
        exclude_doc_ids: List[str] = None,
        similarity_threshold: float = 0.8,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """高度な類似ドキュメント検索"""
        try:
            # キャッシュキー生成
            import hashlib
            cache_key = f"similar_docs:{hashlib.md5(reference_text.encode()).hexdigest()}"
            
            # キャッシュ確認
            cached_results = await self.redis_repo.get(cache_key)
            if cached_results:
                return cached_results
            
            # エンベディング生成
            reference_embedding = await ollama_client.generate_embedding(reference_text)
            if not reference_embedding:
                return []
            
            # ベクトル検索
            vector_results = await self.milvus_repo.search_vectors(
                reference_embedding, 
                max_results * 3  # より多く取得してフィルタリング
            )
            
            # 除外するドキュメントをフィルタ
            if exclude_doc_ids:
                vector_results = [
                    result for result in vector_results 
                    if result.document_id not in exclude_doc_ids
                ]
            
            # 類似度でフィルタ
            filtered_results = [
                result for result in vector_results 
                if result.score >= similarity_threshold
            ]
            
            # ドキュメント情報取得と結果構築
            similar_docs = []
            doc_ids = [result.document_id for result in filtered_results[:max_results]]
            documents = await self.mongo_repo.get_documents_by_ids(doc_ids)
            doc_dict = {doc.id: doc for doc in documents}
            
            for result in filtered_results[:max_results]:
                if result.document_id in doc_dict:
                    doc = doc_dict[result.document_id]
                    
                    # 追加の類似性分析
                    similarity_analysis = await ollama_client.analyze_document_relations(
                        reference_text[:500], 
                        doc.content[:500]
                    )
                    
                    similar_docs.append({
                        "document_id": result.document_id,
                        "title": doc.title,
                        "similarity_score": result.score,
                        "content_preview": doc.content[:300],
                        "file_type": doc.file_type,
                        "tags": doc.tags,
                        "relationship_analysis": similarity_analysis,
                        "metadata": doc.metadata
                    })
            
            # 結果をキャッシュ
            await self.redis_repo.set(cache_key, similar_docs, expire_time=600)  # 10分
            
            logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Failed to find similar documents: {e}")
            return []

    async def natural_language_query(self, question: str) -> Dict[str, Any]:
        """自然言語クエリ処理"""
        try:
            # Neo4jでの自然言語クエリ
            graph_answer = await self.neo4j_repo.natural_language_query(question)
            
            # ベクトル検索での関連情報取得
            search_results = await self.intelligent_search(question, limit=5)
            
            # 回答生成
            context = "\n".join([result.content for result in search_results[:3]])
            
            answer_prompt = f"""
以下の質問に、提供されたコンテキストを基に回答してください：

質問: {question}

コンテキスト:
{context}

グラフ情報: {graph_answer}

回答:
"""
            
            answer = await ollama_client.generate_text(answer_prompt, max_tokens=800)
            
            return {
                "question": question,
                "answer": answer,
                "sources": search_results,
                "graph_info": graph_answer,
                "confidence": self._calculate_confidence(search_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to process natural language query: {e}")
            return {
                "question": question,
                "answer": "申し訳ありませんが、回答を生成できませんでした。",
                "sources": [],
                "graph_info": "",
                "confidence": 0.0
            }
    
    def _calculate_confidence(self, results: List[SearchResult]) -> float:
        """回答信頼度計算"""
        if not results:
            return 0.0
        
        # 上位結果のスコア平均
        top_scores = [result.score for result in results[:3]]
        return sum(top_scores) / len(top_scores)
    
    async def get_enhanced_system_stats(self) -> Dict[str, Any]:
        """拡張システム統計"""
        try:
            base_stats = await self.get_system_stats()
            
            # Ollama統計追加
            ollama_stats = await ollama_client.get_performance_stats()
            
            # Neo4j拡張統計
            neo4j_enhanced_stats = await self.neo4j_repo.get_enhanced_graph_stats()
            
            return {
                **base_stats,
                "ollama_performance": ollama_stats,
                "neo4j_enhanced": neo4j_enhanced_stats,
                "llamaindex_status": {
                    "vector_index_ready": self.vector_index is not None,
                    "query_engine_ready": self.query_engine is not None,
                    "retriever_ready": self.retriever is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get enhanced system stats: {e}")
            return {}
    
    # 基本メソッドを継承
    async def get_system_stats(self) -> Dict[str, Any]:
        """基本システム統計取得"""
        try:
            tasks = [
                self.mongo_repo.get_collection_stats(),
                self.milvus_repo.get_collection_stats(),
                self.neo4j_repo.get_enhanced_graph_stats(),
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
    
    # その他の基本メソッドも必要に応じて実装
    async def _load_file(self, file_path: str) -> List[Document]:
        """ファイル読み込み（基本実装を使用）"""
        # document_service.pyの実装をコピー
        # ...existing code...
        pass
    
    async def _save_document(self, document: Document) -> str:
        """ドキュメント保存（基本実装を使用）"""
        # document_service.pyの実装をコピー
        # ...existing code...
        pass
    
    async def _text_search(self, query: str, filters: Dict[str, Any], limit: int) -> List[SearchResult]:
        """テキスト検索（基本実装を使用）"""
        # document_service.pyの実装をコピー
        # ...existing code...
        pass
    
    async def _merge_search_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """検索結果マージ（基本実装を使用）"""
        # document_service.pyの実装をコピー
        # ...existing code...
        pass
    
    async def _analyze_and_create_relations_enhanced(self, document: Document):
        """拡張関係性分析"""
        # 基本実装 + 拡張機能
        # ...existing code...
        pass
    
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
            logger.info("Enhanced document service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during enhanced shutdown: {e}")