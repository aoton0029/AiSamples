import hashlib
import uuid
from typing import List, Dict, Any, Optional, Tuple
from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

from .ollama_connector import OllamaConnector
from .mongo_client import MongoClient
from .milvus_client import MilvusClient
from .neo4j_client import Neo4jClient
from .redis_client import RedisClient
from .multi_format_loader import MultiFormatLoader


class IndexManager:
    """LlamaIndexとマルチDB統合管理クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        設定を元に各DBクライアントを初期化
        """
        self.config = config or {}
        
        # 各クライアントを初期化
        self.ollama = OllamaConnector(
            base_url=self.config.get("ollama_url", "http://localhost:11434")
        )
        
        self.mongo = MongoClient(
            connection_string=self.config.get("mongo_url", "mongodb://localhost:27017"),
            database_name=self.config.get("mongo_db", "rag_system")
        )
        
        self.milvus = MilvusClient(
            host=self.config.get("milvus_host", "localhost"),
            port=self.config.get("milvus_port", "19530"),
            collection_name=self.config.get("milvus_collection", "document_vectors")
        )
        
        self.neo4j = Neo4jClient(
            uri=self.config.get("neo4j_uri", "bolt://localhost:7687"),
            user=self.config.get("neo4j_user", "neo4j"),
            password=self.config.get("neo4j_password", "password")
        )
        
        self.redis = RedisClient(
            host=self.config.get("redis_host", "localhost"),
            port=self.config.get("redis_port", 6379),
            db=self.config.get("redis_db", 0)
        )
        
        self.loader = MultiFormatLoader()
        
        # LlamaIndex設定
        self._setup_llamaindex()
        
        # Milvusコレクション初期化
        self.milvus.create_collection(dimension=self.config.get("embedding_dim", 768))
        
    def _setup_llamaindex(self):
        """LlamaIndexの設定"""
        # LLMと埋め込みモデルを初期化
        llm = self.ollama.initialize_llm(
            self.config.get("llm_model", "llama3.2:3b")
        )
        embedding_model = self.ollama.initialize_embedding(
            self.config.get("embedding_model", "nomic-embed-text")
        )
        
        # グローバル設定
        Settings.llm = llm
        Settings.embed_model = embedding_model
        
        # テキスト分割設定
        self.text_splitter = SentenceSplitter(
            chunk_size=self.config.get("chunk_size", 1024),
            chunk_overlap=self.config.get("chunk_overlap", 20)
        )
    
    def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """ドキュメントを全DBに追加"""
        document_id = str(uuid.uuid4())
        
        try:
            # 1. ドキュメントを読み込み
            documents = self.loader.load_document(file_path, metadata)
            if not documents:
                raise ValueError("ドキュメントの読み込みに失敗しました")
            
            # 2. テキストを結合
            full_text = "\n".join(doc.text for doc in documents)
            combined_metadata = documents[0].metadata if documents else {}
            combined_metadata.update(metadata or {})
            
            # 3. MongoDBにメタデータとテキストを保存
            self.mongo.save_document(document_id, full_text, combined_metadata)
            
            # 4. テキストを分割してチャンク化
            text_chunks = self.text_splitter.split_text(full_text)
            
            # 5. 埋め込みベクトルを生成
            embeddings = []
            for chunk in text_chunks:
                embedding = Settings.embed_model.get_text_embedding(chunk)
                embeddings.append(embedding)
            
            # 6. Milvusに埋め込みベクトルを保存
            self.milvus.insert_vectors(document_id, text_chunks, embeddings)
            
            # 7. Redisに埋め込みベクトルをキャッシュ
            self.redis.set_document_embeddings(document_id, embeddings)
            
            # 8. Neo4jにドキュメントノードを作成
            title = combined_metadata.get("file_name", "Unknown Document")
            self.neo4j.create_document_node(document_id, title, combined_metadata)
            
            print(f"ドキュメント追加完了: {document_id}")
            return document_id
            
        except Exception as e:
            print(f"ドキュメント追加エラー: {e}")
            # ロールバック処理
            self._cleanup_failed_document(document_id)
            raise
    
    def add_directory(self, directory_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """ディレクトリ内のドキュメントを一括追加"""
        documents = self.loader.load_directory(directory_path, metadata=metadata)
        document_ids = []
        
        for doc in documents:
            try:
                # 一時ファイルとして保存して個別処理
                temp_metadata = doc.metadata.copy() if doc.metadata else {}
                temp_metadata.update(metadata or {})
                
                doc_id = self._add_single_document(doc.text, temp_metadata)
                document_ids.append(doc_id)
                
            except Exception as e:
                print(f"ドキュメント追加エラー: {e}")
                continue
        
        return document_ids
    
    def _add_single_document(self, text: str, metadata: Dict[str, Any]) -> str:
        """単一テキストドキュメントを追加"""
        document_id = str(uuid.uuid4())
        
        # MongoDBに保存
        self.mongo.save_document(document_id, text, metadata)
        
        # テキスト分割と埋め込み
        text_chunks = self.text_splitter.split_text(text)
        embeddings = []
        for chunk in text_chunks:
            embedding = Settings.embed_model.get_text_embedding(chunk)
            embeddings.append(embedding)
        
        # Milvusに保存
        self.milvus.insert_vectors(document_id, text_chunks, embeddings)
        
        # Redisにキャッシュ
        self.redis.set_document_embeddings(document_id, embeddings)
        
        # Neo4jにノード作成
        title = metadata.get("file_name", f"Document_{document_id[:8]}")
        self.neo4j.create_document_node(document_id, title, metadata)
        
        return document_id
    
    def search_similar(self, query: str, top_k: int = 5, 
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """類似検索を実行"""
        # クエリハッシュを生成してキャッシュチェック
        query_hash = hashlib.md5(f"{query}_{top_k}_{filter_metadata}".encode()).hexdigest()
        
        # Redisキャッシュから検索
        cached_results = self.redis.get_search_results(query_hash)
        if cached_results:
            return cached_results
        
        # クエリの埋め込みベクトルを生成
        query_embedding = Settings.embed_model.get_text_embedding(query)
        
        # Milvusで類似検索
        milvus_results = self.milvus.search_similar(
            query_embedding, top_k=top_k * 2  # 多めに取得してフィルタリング
        )
        
        # MongoDBからメタデータを取得してフィルタリング
        filtered_results = []
        for result in milvus_results:
            doc_id = result["document_id"]
            mongo_doc = self.mongo.get_document(doc_id)
            
            if mongo_doc:
                # メタデータフィルタリング
                if filter_metadata:
                    if not self._match_metadata_filter(mongo_doc.get("metadata", {}), filter_metadata):
                        continue
                
                filtered_results.append({
                    "document_id": doc_id,
                    "chunk_id": result["chunk_id"],
                    "text": result["text"],
                    "score": result["score"],
                    "metadata": mongo_doc.get("metadata", {})
                })
                
                if len(filtered_results) >= top_k:
                    break
        
        # 結果をキャッシュ
        self.redis.set_search_results(query_hash, filtered_results)
        
        return filtered_results
    
    def query_with_rag(self, query: str, top_k: int = 5) -> str:
        """RAGを使用してクエリに回答"""
        # クエリハッシュでキャッシュチェック
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cached_response = self.redis.get_llm_response(query_hash)
        if cached_response:
            return cached_response
        
        # 類似検索を実行
        search_results = self.search_similar(query, top_k)
        
        if not search_results:
            return "関連するドキュメントが見つかりませんでした。"
        
        # コンテキストを構築
        context_texts = [result["text"] for result in search_results]
        context = "\n\n".join(context_texts)
        
        # プロンプトを作成
        prompt = f"""
以下のコンテキストを参考にして、質問に答えてください。

コンテキスト:
{context}

質問: {query}

回答:
"""
        
        # LLMで回答生成
        response = Settings.llm.complete(prompt)
        response_text = str(response)
        
        # レスポンスをキャッシュ
        self.redis.cache_llm_response(query_hash, response_text)
        
        return response_text
    
    def find_related_documents(self, document_id: str) -> List[Dict[str, Any]]:
        """Neo4jを使用して関連ドキュメントを検索"""
        return self.neo4j.find_related_documents(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """全DBからドキュメントを削除"""
        try:
            # MongoDB
            self.mongo.delete_document(document_id)
            
            # Milvus
            self.milvus.delete_document_vectors(document_id)
            
            # Neo4j
            self.neo4j.delete_document_graph(document_id)
            
            # Redis (関連キャッシュ)
            embedding_key = f"embeddings:{document_id}"
            self.redis.delete_cache(embedding_key)
            
            return True
        except Exception as e:
            print(f"ドキュメント削除エラー: {e}")
            return False
    
    def _cleanup_failed_document(self, document_id: str):
        """失敗したドキュメント追加のクリーンアップ"""
        try:
            self.delete_document(document_id)
        except:
            pass
    
    def _match_metadata_filter(self, metadata: Dict[str, Any], 
                             filter_criteria: Dict[str, Any]) -> bool:
        """メタデータフィルタリング"""
        for key, value in filter_criteria.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def get_system_stats(self) -> Dict[str, Any]:
        """システム統計情報を取得"""
        return {
            "mongo_documents": len(self.mongo.get_all_documents()),
            "milvus_stats": self.milvus.get_collection_stats(),
            "redis_keys": len(self.redis.get_keys_by_pattern("*")),
            "ollama_connection": self.ollama.check_connection()
        }
    
    def close_connections(self):
        """全DB接続を閉じる"""
        try:
            self.mongo.close()
            self.neo4j.close()
            self.redis.close()
        except Exception as e:
            print(f"接続クローズエラー: {e}")