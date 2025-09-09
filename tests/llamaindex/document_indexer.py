import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.extractors import (
    TitleExtractor,
    KeywordExtractor,
    SummaryExtractor,
)
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.core.schema import BaseNode, MetadataMode
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core.extractors import EntityExtractor
from llama_index.core.graph_stores import SimpleGraphStore

from .ollama_connector import OllamaConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIndexer:
    """ドキュメントのマルチDB索引化を行うクラス"""
    
    def __init__(
        self,
        ollama_connector: OllamaConnector,
        milvus_config: Dict[str, Any],
        mongo_config: Dict[str, Any],
        neo4j_config: Dict[str, Any],
        chunk_size: int = 1024,
        chunk_overlap: int = 200
    ):
        self.ollama = ollama_connector
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 各DBストアの初期化
        self.vector_store = self._init_vector_store(milvus_config)
        self.doc_store = self._init_document_store(mongo_config)
        self.graph_store = self._init_graph_store(neo4j_config)
        
        # ノードパーサーの初期化
        self.node_parser = self._init_node_parser()
        
        # メタデータ抽出器の初期化
        self.extractors = self._init_extractors()
        
        # ストレージコンテキストの設定
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store,
            docstore=self.doc_store,
            graph_store=self.graph_store
        )
    
    def _init_vector_store(self, config: Dict[str, Any]) -> MilvusVectorStore:
        """Milvusベクトルストアの初期化"""
        return MilvusVectorStore(
            uri=config.get("uri", "http://localhost:19530"),
            collection_name=config.get("collection_name", "documents"),
            dim=config.get("dimension", 768),
            similarity_metric=config.get("similarity_metric", "IP")
        )
    
    def _init_document_store(self, config: Dict[str, Any]) -> MongoDocumentStore:
        """MongoDBドキュメントストアの初期化"""
        return MongoDocumentStore.from_uri(
            uri=config.get("uri", "mongodb://localhost:27017"),
            db_name=config.get("db_name", "document_db"),
            namespace=config.get("namespace", "documents")
        )
    
    def _init_graph_store(self, config: Dict[str, Any]) -> Neo4jGraphStore:
        """Neo4jグラフストアの初期化"""
        return Neo4jGraphStore(
            username=config.get("username", "neo4j"),
            password=config.get("password", "password"),
            url=config.get("url", "bolt://localhost:7687"),
            database=config.get("database", "neo4j")
        )
    
    def _init_node_parser(self) -> SentenceSplitter:
        """ノードパーサーの初期化"""
        return SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def _init_extractors(self) -> List[Any]:
        """メタデータ抽出器の初期化"""
        if not self.ollama.llm:
            self.ollama.initialize_llm()
        
        return [
            TitleExtractor(llm=self.ollama.llm),
            KeywordExtractor(keywords=10, llm=self.ollama.llm),
            SummaryExtractor(summaries=["prev", "self"], llm=self.ollama.llm),
            EntityExtractor(prediction_threshold=0.5, llm=self.ollama.llm)
        ]
    
    def preprocess_document(self, document: Document) -> Document:
        """1. 前処理：正規化とメタデータ抽出"""
        logger.info(f"前処理開始: {document.metadata.get('title', 'Unknown')}")
        
        # ドキュメントIDの生成
        if 'doc_id' not in document.metadata:
            document.metadata['doc_id'] = str(uuid.uuid4())
        
        # タイムスタンプの追加
        document.metadata['indexed_at'] = datetime.utcnow().isoformat()
        
        # 基本メタデータの正規化
        document.metadata.setdefault('title', 'Untitled')
        document.metadata.setdefault('author', 'Unknown')
        document.metadata.setdefault('source', 'Unknown')
        document.metadata.setdefault('tags', [])
        
        return document
    
    def chunk_document(self, document: Document) -> List[BaseNode]:
        """チャンク化処理"""
        logger.info(f"チャンク化開始: {document.metadata.get('doc_id')}")
        
        # ドキュメントをノードに変換
        nodes = self.node_parser.get_nodes_from_documents([document])
        
        # 各ノードにdoc_idを継承
        doc_id = document.metadata.get('doc_id')
        for node in nodes:
            node.metadata['doc_id'] = doc_id
            node.metadata['chunk_id'] = str(uuid.uuid4())
        
        return nodes
    
    def extract_metadata(self, nodes: List[BaseNode]) -> List[BaseNode]:
        """2. メタデータ抽出"""
        logger.info(f"メタデータ抽出開始: {len(nodes)}個のノード")
        
        # メタデータ抽出器を順次適用
        for extractor in self.extractors:
            try:
                nodes = extractor.extract(nodes)
            except Exception as e:
                logger.warning(f"メタデータ抽出エラー ({extractor.__class__.__name__}): {e}")
        
        return nodes
    
    def generate_embeddings(self, nodes: List[BaseNode]) -> List[BaseNode]:
        """3. 埋め込み生成"""
        logger.info(f"埋め込み生成開始: {len(nodes)}個のノード")
        
        if not self.ollama.embedding_model:
            self.ollama.initialize_embedding()
        
        # ノードに埋め込みを追加
        for node in nodes:
            try:
                text = node.get_content(metadata_mode=MetadataMode.EMBED)
                embedding = self.ollama.embedding_model.get_text_embedding(text)
                node.embedding = embedding
            except Exception as e:
                logger.error(f"埋め込み生成エラー (node {node.node_id}): {e}")
        
        return nodes
    
    def save_to_document_db(self, nodes: List[BaseNode]) -> bool:
        """4. ドキュメントDB保存"""
        logger.info(f"ドキュメントDB保存開始: {len(nodes)}個のノード")
        
        try:
            # ノードをドキュメントストアに保存
            for node in nodes:
                self.doc_store.add_documents([node])
            
            logger.info("ドキュメントDB保存完了")
            return True
        except Exception as e:
            logger.error(f"ドキュメントDB保存エラー: {e}")
            return False
    
    def save_to_vector_db(self, nodes: List[BaseNode]) -> bool:
        """5. ベクトルDB保存"""
        logger.info(f"ベクトルDB保存開始: {len(nodes)}個のノード")
        
        try:
            # ベクトルストアに保存
            self.vector_store.add(nodes)
            
            logger.info("ベクトルDB保存完了")
            return True
        except Exception as e:
            logger.error(f"ベクトルDB保存エラー: {e}")
            return False
    
    def extract_and_save_entities(self, nodes: List[BaseNode]) -> bool:
        """6. エンティティ抽出とグラフDB保存"""
        logger.info(f"エンティティ抽出・グラフDB保存開始: {len(nodes)}個のノード")
        
        try:
            for node in nodes:
                doc_id = node.metadata.get('doc_id')
                
                # エンティティの抽出
                entities = node.metadata.get('entities', [])
                
                # エンティティをグラフノードとして保存
                for entity in entities:
                    entity_id = f"entity_{hash(entity)}"
                    
                    # エンティティノードの作成
                    self.graph_store.upsert_triplet(
                        subj=entity_id,
                        rel="IS_ENTITY",
                        obj=entity,
                        subj_props={"type": "entity", "name": entity, "doc_id": doc_id},
                        obj_props={"type": "label"}
                    )
                    
                    # ドキュメントとエンティティの関係
                    self.graph_store.upsert_triplet(
                        subj=doc_id,
                        rel="CONTAINS_ENTITY",
                        obj=entity_id,
                        subj_props={"type": "document", "doc_id": doc_id},
                        obj_props={"type": "entity", "name": entity}
                    )
            
            logger.info("グラフDB保存完了")
            return True
        except Exception as e:
            logger.error(f"グラフDB保存エラー: {e}")
            return False
    
    def index_document(self, document: Document) -> Dict[str, Any]:
        """ドキュメントの完全インデックス化"""
        logger.info(f"ドキュメントインデックス化開始: {document.metadata.get('title', 'Unknown')}")
        
        result = {
            "success": False,
            "doc_id": None,
            "errors": [],
            "stages_completed": []
        }
        
        try:
            # 1. 前処理
            document = self.preprocess_document(document)
            result["doc_id"] = document.metadata.get('doc_id')
            result["stages_completed"].append("preprocess")
            
            # 2. チャンク化
            nodes = self.chunk_document(document)
            result["stages_completed"].append("chunk")
            
            # 3. メタデータ抽出
            nodes = self.extract_metadata(nodes)
            result["stages_completed"].append("metadata_extraction")
            
            # 4. 埋め込み生成
            nodes = self.generate_embeddings(nodes)
            result["stages_completed"].append("embedding_generation")
            
            # 5. ドキュメントDB保存
            if self.save_to_document_db(nodes):
                result["stages_completed"].append("document_db_save")
            else:
                result["errors"].append("document_db_save_failed")
            
            # 6. ベクトルDB保存
            if self.save_to_vector_db(nodes):
                result["stages_completed"].append("vector_db_save")
            else:
                result["errors"].append("vector_db_save_failed")
            
            # 7. グラフDB保存
            if self.extract_and_save_entities(nodes):
                result["stages_completed"].append("graph_db_save")
            else:
                result["errors"].append("graph_db_save_failed")
            
            # 成功判定
            if len(result["errors"]) == 0:
                result["success"] = True
                logger.info(f"ドキュメントインデックス化完了: {result['doc_id']}")
            else:
                logger.warning(f"ドキュメントインデックス化部分的失敗: {result['errors']}")
            
        except Exception as e:
            logger.error(f"ドキュメントインデックス化エラー: {e}")
            result["errors"].append(f"unexpected_error: {str(e)}")
        
        return result
    
    def batch_index_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """バッチドキュメントインデックス化"""
        logger.info(f"バッチインデックス化開始: {len(documents)}個のドキュメント")
        
        results = []
        for i, document in enumerate(documents):
            logger.info(f"処理中 {i+1}/{len(documents)}")
            result = self.index_document(document)
            results.append(result)
        
        # 統計情報のログ出力
        successful = sum(1 for r in results if r["success"])
        logger.info(f"バッチインデックス化完了: {successful}/{len(documents)} 成功")
        
        return results
    
    def check_duplicate(self, document: Document) -> Optional[str]:
        """重複検出"""
        # タイトルと作成者による重複チェック
        title = document.metadata.get('title')
        author = document.metadata.get('author')
        
        if title and author:
            # ここで実際の重複検索ロジックを実装
            # 簡単な例として、メタデータベースの検索
            pass
        
        return None
    
    def get_indexing_stats(self) -> Dict[str, Any]:
        """インデックス化統計の取得"""
        try:
            # 各DBの統計情報を取得
            stats = {
                "vector_store": {
                    "total_vectors": "N/A"  # Milvusから取得
                },
                "document_store": {
                    "total_documents": "N/A"  # MongoDBから取得
                },
                "graph_store": {
                    "total_nodes": "N/A",  # Neo4jから取得
                    "total_relationships": "N/A"
                }
            }
            
            return stats
        except Exception as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {}


def demo():
    from llama_index.core import Document
    from core.ollama_connector import OllamaConnector
    from core.document_indexer import DocumentIndexer
    from core.config import (
        DEFAULT_MILVUS_CONFIG,
        DEFAULT_MONGO_CONFIG,
        DEFAULT_NEO4J_CONFIG,
        DEFAULT_INDEXER_CONFIG
    )

    def main():
        # Ollamaコネクターの初期化
        ollama = OllamaConnector()
        
        # LLMと埋め込みモデルの初期化
        ollama.initialize_llm(DEFAULT_INDEXER_CONFIG["llm_model"])
        ollama.initialize_embedding(DEFAULT_INDEXER_CONFIG["embedding_model"])
        
        # ドキュメントインデクサーの初期化
        indexer = DocumentIndexer(
            ollama_connector=ollama,
            milvus_config=DEFAULT_MILVUS_CONFIG,
            mongo_config=DEFAULT_MONGO_CONFIG,
            neo4j_config=DEFAULT_NEO4J_CONFIG,
            chunk_size=DEFAULT_INDEXER_CONFIG["chunk_size"],
            chunk_overlap=DEFAULT_INDEXER_CONFIG["chunk_overlap"]
        )
        
        # サンプルドキュメントの作成
        sample_documents = [
            Document(
                text="これは人工知能に関する技術文書です。機械学習やディープラーニングについて詳しく説明しています。",
                metadata={
                    "title": "AI技術概要",
                    "author": "田中太郎",
                    "source": "tech_blog",
                    "tags": ["AI", "機械学習", "技術"]
                }
            ),
            Document(
                text="データサイエンスの基礎について学習します。統計学やデータ分析の手法を網羅的に扱います。",
                metadata={
                    "title": "データサイエンス入門",
                    "author": "山田花子",
                    "source": "educational_material",
                    "tags": ["データサイエンス", "統計学", "分析"]
                }
            )
        ]
        
        # 単一ドキュメントのインデックス化
        print("=== 単一ドキュメントインデックス化 ===")
        result = indexer.index_document(sample_documents[0])
        print(f"結果: {result}")
        
        # バッチインデックス化
        print("\n=== バッチインデックス化 ===")
        batch_results = indexer.batch_index_documents(sample_documents)
        for i, result in enumerate(batch_results):
            print(f"ドキュメント {i+1}: {result}")
        
        # 統計情報の取得
        print("\n=== インデックス化統計 ===")
        stats = indexer.get_indexing_stats()
        print(f"統計情報: {stats}")

    if __name__ == "__main__":
        main()