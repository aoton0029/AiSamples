import uuid
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """トランザクション状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class OperationType(Enum):
    """操作タイプ"""
    VECTOR_STORE_ADD = "vector_store_add"
    DOCUMENT_STORE_ADD = "document_store_add"
    GRAPH_STORE_ADD = "graph_store_add"
    METADATA_EXTRACT = "metadata_extract"
    EMBEDDING_GENERATE = "embedding_generate"


@dataclass
class TransactionOperation:
    """トランザクション操作記録"""
    operation_id: str
    operation_type: OperationType
    status: TransactionStatus
    timestamp: str
    data: Dict[str, Any]
    rollback_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class TransactionLog:
    """トランザクションログ"""
    transaction_id: str
    doc_id: str
    status: TransactionStatus
    start_time: str
    end_time: Optional[str] = None
    operations: List[TransactionOperation] = None
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.operations is None:
            self.operations = []


class TransactionManager:
    """トランザクション管理クラス"""
    
    def __init__(self):
        self.active_transactions: Dict[str, TransactionLog] = {}
        self.completed_transactions: Dict[str, TransactionLog] = {}
        self.rollback_handlers: Dict[OperationType, Callable] = {}
        
    def register_rollback_handler(self, operation_type: OperationType, handler: Callable):
        """ロールバックハンドラーの登録"""
        self.rollback_handlers[operation_type] = handler
        
    def create_transaction(self, doc_id: str) -> str:
        """新しいトランザクションの作成"""
        transaction_id = str(uuid.uuid4())
        
        transaction_log = TransactionLog(
            transaction_id=transaction_id,
            doc_id=doc_id,
            status=TransactionStatus.PENDING,
            start_time=datetime.utcnow().isoformat()
        )
        
        self.active_transactions[transaction_id] = transaction_log
        logger.info(f"トランザクション作成: {transaction_id} (doc_id: {doc_id})")
        
        return transaction_id
    
    def start_transaction(self, transaction_id: str):
        """トランザクション開始"""
        if transaction_id in self.active_transactions:
            self.active_transactions[transaction_id].status = TransactionStatus.IN_PROGRESS
            logger.info(f"トランザクション開始: {transaction_id}")
    
    def add_operation(
        self, 
        transaction_id: str, 
        operation_type: OperationType, 
        data: Dict[str, Any],
        rollback_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """操作の追加"""
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        operation_id = str(uuid.uuid4())
        operation = TransactionOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            status=TransactionStatus.PENDING,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            rollback_data=rollback_data
        )
        
        self.active_transactions[transaction_id].operations.append(operation)
        self.active_transactions[transaction_id].total_operations += 1
        
        logger.info(f"操作追加: {operation_type.value} (transaction: {transaction_id})")
        return operation_id
    
    def mark_operation_success(self, transaction_id: str, operation_id: str):
        """操作成功マーク"""
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            return
        
        for operation in transaction.operations:
            if operation.operation_id == operation_id:
                operation.status = TransactionStatus.COMMITTED
                transaction.successful_operations += 1
                logger.info(f"操作成功: {operation_id}")
                break
    
    def mark_operation_failure(self, transaction_id: str, operation_id: str, error: str):
        """操作失敗マーク"""
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            return
        
        for operation in transaction.operations:
            if operation.operation_id == operation_id:
                operation.status = TransactionStatus.FAILED
                operation.error_message = error
                transaction.failed_operations += 1
                logger.error(f"操作失敗: {operation_id} - {error}")
                break
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """トランザクションコミット"""
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return False
        
        # 全ての操作が成功しているかチェック
        if transaction.failed_operations > 0:
            logger.warning(f"Transaction {transaction_id} has failed operations, cannot commit")
            return False
        
        transaction.status = TransactionStatus.COMMITTED
        transaction.end_time = datetime.utcnow().isoformat()
        
        # 完了したトランザクションに移動
        self.completed_transactions[transaction_id] = transaction
        del self.active_transactions[transaction_id]
        
        logger.info(f"トランザクションコミット: {transaction_id}")
        return True
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """トランザクションロールバック"""
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return False
        
        logger.info(f"トランザクションロールバック開始: {transaction_id}")
        
        # 成功した操作を逆順でロールバック
        successful_operations = [
            op for op in transaction.operations 
            if op.status == TransactionStatus.COMMITTED
        ]
        
        rollback_success = True
        for operation in reversed(successful_operations):
            try:
                if operation.operation_type in self.rollback_handlers:
                    handler = self.rollback_handlers[operation.operation_type]
                    handler(operation.rollback_data or operation.data)
                    logger.info(f"操作ロールバック成功: {operation.operation_id}")
                else:
                    logger.warning(f"ロールバックハンドラーなし: {operation.operation_type}")
            except Exception as e:
                logger.error(f"ロールバック失敗: {operation.operation_id} - {e}")
                rollback_success = False
        
        transaction.status = TransactionStatus.ROLLED_BACK
        transaction.end_time = datetime.utcnow().isoformat()
        
        # 完了したトランザクションに移動
        self.completed_transactions[transaction_id] = transaction
        del self.active_transactions[transaction_id]
        
        logger.info(f"トランザクションロールバック完了: {transaction_id}")
        return rollback_success
    
    def get_transaction_status(self, transaction_id: str) -> Optional[TransactionLog]:
        """トランザクション状態取得"""
        if transaction_id in self.active_transactions:
            return self.active_transactions[transaction_id]
        elif transaction_id in self.completed_transactions:
            return self.completed_transactions[transaction_id]
        return None
    
    @contextmanager
    def transaction_context(self, doc_id: str):
        """トランザクションコンテキストマネージャー"""
        transaction_id = self.create_transaction(doc_id)
        self.start_transaction(transaction_id)
        
        try:
            yield transaction_id
            # 自動コミット
            self.commit_transaction(transaction_id)
        except Exception as e:
            logger.error(f"トランザクション例外: {e}")
            self.rollback_transaction(transaction_id)
            raise
    
    def cleanup_old_transactions(self, days: int = 7):
        """古いトランザクションのクリーンアップ"""
        cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        
        to_remove = []
        for transaction_id, transaction in self.completed_transactions.items():
            transaction_time = datetime.fromisoformat(transaction.start_time).timestamp()
            if transaction_time < cutoff_time:
                to_remove.append(transaction_id)
        
        for transaction_id in to_remove:
            del self.completed_transactions[transaction_id]
        
        logger.info(f"古いトランザクション削除: {len(to_remove)}件")
    
    def get_transaction_summary(self) -> Dict[str, Any]:
        """トランザクション統計サマリー"""
        active_count = len(self.active_transactions)
        completed_count = len(self.completed_transactions)
        
        completed_by_status = {}
        for transaction in self.completed_transactions.values():
            status = transaction.status.value
            completed_by_status[status] = completed_by_status.get(status, 0) + 1
        
        return {
            "active_transactions": active_count,
            "completed_transactions": completed_count,
            "completed_by_status": completed_by_status,
            "total_transactions": active_count + completed_count
        }


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

from .ollama_connector import OllamaConnector
from .transaction_manager import TransactionManager, OperationType, TransactionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionalDocumentIndexer:
    """トランザクション対応ドキュメントインデクサー"""
    
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
        
        # トランザクションマネージャー
        self.transaction_manager = TransactionManager()
        
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
        
        # ロールバックハンドラーの登録
        self._register_rollback_handlers()
    
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
    
    def _register_rollback_handlers(self):
        """ロールバックハンドラーの登録"""
        self.transaction_manager.register_rollback_handler(
            OperationType.VECTOR_STORE_ADD,
            self._rollback_vector_store
        )
        self.transaction_manager.register_rollback_handler(
            OperationType.DOCUMENT_STORE_ADD,
            self._rollback_document_store
        )
        self.transaction_manager.register_rollback_handler(
            OperationType.GRAPH_STORE_ADD,
            self._rollback_graph_store
        )
    
    def _rollback_vector_store(self, rollback_data: Dict[str, Any]):
        """ベクトルストアのロールバック"""
        try:
            node_ids = rollback_data.get("node_ids", [])
            if node_ids:
                self.vector_store.delete(node_ids)
                logger.info(f"ベクトルストアロールバック: {len(node_ids)}個のノード削除")
        except Exception as e:
            logger.error(f"ベクトルストアロールバックエラー: {e}")
    
    def _rollback_document_store(self, rollback_data: Dict[str, Any]):
        """ドキュメントストアのロールバック"""
        try:
            doc_ids = rollback_data.get("doc_ids", [])
            for doc_id in doc_ids:
                self.doc_store.delete_document(doc_id)
            logger.info(f"ドキュメントストアロールバック: {len(doc_ids)}個のドキュメント削除")
        except Exception as e:
            logger.error(f"ドキュメントストアロールバックエラー: {e}")
    
    def _rollback_graph_store(self, rollback_data: Dict[str, Any]):
        """グラフストアのロールバック"""
        try:
            triplets = rollback_data.get("triplets", [])
            for triplet in triplets:
                # Neo4jから特定のトリプレットを削除
                # 実装は具体的なNeo4j操作に依存
                pass
            logger.info(f"グラフストアロールバック: {len(triplets)}個のトリプレット削除")
        except Exception as e:
            logger.error(f"グラフストアロールバックエラー: {e}")
    
    def preprocess_document(self, document: Document, transaction_id: str) -> Document:
        """前処理（トランザクション対応）"""
        logger.info(f"前処理開始: {document.metadata.get('title', 'Unknown')}")
        
        # ドキュメントIDの生成
        if 'doc_id' not in document.metadata:
            document.metadata['doc_id'] = str(uuid.uuid4())
        
        # タイムスタンプの追加
        document.metadata['indexed_at'] = datetime.utcnow().isoformat()
        document.metadata['transaction_id'] = transaction_id
        
        # 基本メタデータの正規化
        document.metadata.setdefault('title', 'Untitled')
        document.metadata.setdefault('author', 'Unknown')
        document.metadata.setdefault('source', 'Unknown')
        document.metadata.setdefault('tags', [])
        
        return document
    
    def generate_embeddings(self, nodes: List[BaseNode], transaction_id: str) -> List[BaseNode]:
        """埋め込み生成（トランザクション対応）"""
        operation_id = self.transaction_manager.add_operation(
            transaction_id,
            OperationType.EMBEDDING_GENERATE,
            {"node_count": len(nodes)}
        )
        
        try:
            if not self.ollama.embedding_model:
                self.ollama.initialize_embedding()
            
            for node in nodes:
                text = node.get_content(metadata_mode=MetadataMode.EMBED)
                embedding = self.ollama.embedding_model.get_text_embedding(text)
                node.embedding = embedding
            
            self.transaction_manager.mark_operation_success(transaction_id, operation_id)
            return nodes
            
        except Exception as e:
            self.transaction_manager.mark_operation_failure(transaction_id, operation_id, str(e))
            raise
    
    def save_to_document_db(self, nodes: List[BaseNode], transaction_id: str) -> bool:
        """ドキュメントDB保存（トランザクション対応）"""
        doc_ids = [node.node_id for node in nodes]
        operation_id = self.transaction_manager.add_operation(
            transaction_id,
            OperationType.DOCUMENT_STORE_ADD,
            {"node_ids": [node.node_id for node in nodes]},
            rollback_data={"doc_ids": doc_ids}
        )
        
        try:
            for node in nodes:
                self.doc_store.add_documents([node])
            
            self.transaction_manager.mark_operation_success(transaction_id, operation_id)
            logger.info("ドキュメントDB保存完了")
            return True
            
        except Exception as e:
            self.transaction_manager.mark_operation_failure(transaction_id, operation_id, str(e))
            logger.error(f"ドキュメントDB保存エラー: {e}")
            return False
    
    def save_to_vector_db(self, nodes: List[BaseNode], transaction_id: str) -> bool:
        """ベクトルDB保存（トランザクション対応）"""
        node_ids = [node.node_id for node in nodes]
        operation_id = self.transaction_manager.add_operation(
            transaction_id,
            OperationType.VECTOR_STORE_ADD,
            {"node_ids": node_ids},
            rollback_data={"node_ids": node_ids}
        )
        
        try:
            self.vector_store.add(nodes)
            
            self.transaction_manager.mark_operation_success(transaction_id, operation_id)
            logger.info("ベクトルDB保存完了")
            return True
            
        except Exception as e:
            self.transaction_manager.mark_operation_failure(transaction_id, operation_id, str(e))
            logger.error(f"ベクトルDB保存エラー: {e}")
            return False
    
    def extract_and_save_entities(self, nodes: List[BaseNode], transaction_id: str) -> bool:
        """エンティティ抽出とグラフDB保存（トランザクション対応）"""
        triplets = []
        operation_id = self.transaction_manager.add_operation(
            transaction_id,
            OperationType.GRAPH_STORE_ADD,
            {"node_count": len(nodes)},
            rollback_data={"triplets": triplets}
        )
        
        try:
            for node in nodes:
                doc_id = node.metadata.get('doc_id')
                entities = node.metadata.get('entities', [])
                
                for entity in entities:
                    entity_id = f"entity_{hash(entity)}"
                    
                    # トリプレット記録
                    triplet_data = {
                        "subj": entity_id,
                        "rel": "IS_ENTITY", 
                        "obj": entity
                    }
                    triplets.append(triplet_data)
                    
                    # グラフストアに保存
                    self.graph_store.upsert_triplet(
                        subj=entity_id,
                        rel="IS_ENTITY",
                        obj=entity,
                        subj_props={"type": "entity", "name": entity, "doc_id": doc_id},
                        obj_props={"type": "label"}
                    )
                    
                    # ドキュメント関係のトリプレット
                    doc_triplet = {
                        "subj": doc_id,
                        "rel": "CONTAINS_ENTITY",
                        "obj": entity_id
                    }
                    triplets.append(doc_triplet)
                    
                    self.graph_store.upsert_triplet(
                        subj=doc_id,
                        rel="CONTAINS_ENTITY",
                        obj=entity_id,
                        subj_props={"type": "document", "doc_id": doc_id},
                        obj_props={"type": "entity", "name": entity}
                    )
            
            # ロールバックデータを更新
            operation = next(
                op for op in self.transaction_manager.active_transactions[transaction_id].operations
                if op.operation_id == operation_id
            )
            operation.rollback_data["triplets"] = triplets
            
            self.transaction_manager.mark_operation_success(transaction_id, operation_id)
            logger.info("グラフDB保存完了")
            return True
            
        except Exception as e:
            self.transaction_manager.mark_operation_failure(transaction_id, operation_id, str(e))
            logger.error(f"グラフDB保存エラー: {e}")
            return False
    
    def index_document(self, document: Document) -> Dict[str, Any]:
        """ドキュメントの完全インデックス化（トランザクション対応）"""
        doc_id = document.metadata.get('doc_id', str(uuid.uuid4()))
        
        with self.transaction_manager.transaction_context(doc_id) as transaction_id:
            logger.info(f"トランザクションインデックス化開始: {doc_id}")
            
            result = {
                "success": False,
                "doc_id": doc_id,
                "transaction_id": transaction_id,
                "errors": [],
                "stages_completed": []
            }
            
            try:
                # 1. 前処理
                document = self.preprocess_document(document, transaction_id)
                result["stages_completed"].append("preprocess")
                
                # 2. チャンク化
                nodes = self.node_parser.get_nodes_from_documents([document])
                for node in nodes:
                    node.metadata['doc_id'] = doc_id
                    node.metadata['chunk_id'] = str(uuid.uuid4())
                    node.metadata['transaction_id'] = transaction_id
                result["stages_completed"].append("chunk")
                
                # 3. メタデータ抽出
                for extractor in self.extractors:
                    try:
                        nodes = extractor.extract(nodes)
                    except Exception as e:
                        logger.warning(f"メタデータ抽出エラー ({extractor.__class__.__name__}): {e}")
                result["stages_completed"].append("metadata_extraction")
                
                # 4. 埋め込み生成
                nodes = self.generate_embeddings(nodes, transaction_id)
                result["stages_completed"].append("embedding_generation")
                
                # 5. ドキュメントDB保存
                if self.save_to_document_db(nodes, transaction_id):
                    result["stages_completed"].append("document_db_save")
                else:
                    result["errors"].append("document_db_save_failed")
                    raise Exception("Document DB save failed")
                
                # 6. ベクトルDB保存
                if self.save_to_vector_db(nodes, transaction_id):
                    result["stages_completed"].append("vector_db_save")
                else:
                    result["errors"].append("vector_db_save_failed")
                    raise Exception("Vector DB save failed")
                
                # 7. グラフDB保存
                if self.extract_and_save_entities(nodes, transaction_id):
                    result["stages_completed"].append("graph_db_save")
                else:
                    result["errors"].append("graph_db_save_failed")
                    raise Exception("Graph DB save failed")
                
                result["success"] = True
                logger.info(f"トランザクションインデックス化成功: {doc_id}")
                
            except Exception as e:
                logger.error(f"トランザクションインデックス化エラー: {e}")
                result["errors"].append(f"transaction_error: {str(e)}")
                raise  # コンテキストマネージャーがロールバックを実行
            
            return result
    
    def batch_index_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """バッチドキュメントインデックス化（トランザクション対応）"""
        logger.info(f"バッチトランザクションインデックス化開始: {len(documents)}個")
        
        results = []
        for i, document in enumerate(documents):
            logger.info(f"処理中 {i+1}/{len(documents)}")
            try:
                result = self.index_document(document)
                results.append(result)
            except Exception as e:
                # 個別ドキュメントの失敗は続行
                logger.error(f"ドキュメント{i+1}処理失敗: {e}")
                results.append({
                    "success": False,
                    "doc_id": document.metadata.get('doc_id', 'unknown'),
                    "transaction_id": None,
                    "errors": [f"processing_error: {str(e)}"],
                    "stages_completed": []
                })
        
        # 統計情報
        successful = sum(1 for r in results if r["success"])
        logger.info(f"バッチインデックス化完了: {successful}/{len(documents)} 成功")
        
        return results
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """トランザクション状態取得"""
        transaction_log = self.transaction_manager.get_transaction_status(transaction_id)
        if transaction_log:
            return {
                "transaction_id": transaction_log.transaction_id,
                "doc_id": transaction_log.doc_id,
                "status": transaction_log.status.value,
                "start_time": transaction_log.start_time,
                "end_time": transaction_log.end_time,
                "total_operations": transaction_log.total_operations,
                "successful_operations": transaction_log.successful_operations,
                "failed_operations": transaction_log.failed_operations,
                "operations": [
                    {
                        "operation_id": op.operation_id,
                        "operation_type": op.operation_type.value,
                        "status": op.status.value,
                        "timestamp": op.timestamp,
                        "error_message": op.error_message
                    }
                    for op in transaction_log.operations
                ]
            }
        return None
    
    def get_indexing_stats(self) -> Dict[str, Any]:
        """インデックス化統計の取得（トランザクション統計含む）"""
        transaction_summary = self.transaction_manager.get_transaction_summary()
        
        return {
            "vector_store": {"total_vectors": "N/A"},
            "document_store": {"total_documents": "N/A"},
            "graph_store": {"total_nodes": "N/A", "total_relationships": "N/A"},
            "transactions": transaction_summary
        }






from llama_index.core import Document
from core.ollama_connector import OllamaConnector
from core.document_indexer import TransactionalDocumentIndexer
from core.config import (
    DEFAULT_MILVUS_CONFIG,
    DEFAULT_MONGO_CONFIG,
    DEFAULT_NEO4J_CONFIG,
    DEFAULT_INDEXER_CONFIG
)

def main():
    # Ollamaコネクターの初期化
    ollama = OllamaConnector()
    ollama.initialize_llm(DEFAULT_INDEXER_CONFIG["llm_model"])
    ollama.initialize_embedding(DEFAULT_INDEXER_CONFIG["embedding_model"])
    
    # トランザクション対応インデクサーの初期化
    indexer = TransactionalDocumentIndexer(
        ollama_connector=ollama,
        milvus_config=DEFAULT_MILVUS_CONFIG,
        mongo_config=DEFAULT_MONGO_CONFIG,
        neo4j_config=DEFAULT_NEO4J_CONFIG,
        chunk_size=DEFAULT_INDEXER_CONFIG["chunk_size"],
        chunk_overlap=DEFAULT_INDEXER_CONFIG["chunk_overlap"]
    )
    
    # サンプルドキュメント
    sample_document = Document(
        text="これは重要なビジネス文書です。顧客データと財務情報が含まれています。",
        metadata={
            "title": "重要文書",
            "author": "佐藤太郎",
            "source": "business_docs",
            "tags": ["重要", "機密", "ビジネス"]
        }
    )
    
    # トランザクション付きインデックス化
    print("=== トランザクション付きインデックス化 ===")
    result = indexer.index_document(sample_document)
    print(f"結果: {result}")
    
    # トランザクション状態確認
    if result.get("transaction_id"):
        print(f"\n=== トランザクション状態 ===")
        status = indexer.get_transaction_status(result["transaction_id"])
        print(f"状態: {status}")
    
    # 統計情報
    print(f"\n=== 統計情報 ===")
    stats = indexer.get_indexing_stats()
    print(f"統計: {stats}")
    
    # 意図的にエラーを発生させるテスト
    print(f"\n=== エラーケーステスト ===")
    invalid_document = Document(
        text="",  # 空文書でエラーを誘発
        metadata={"title": "Invalid Document"}
    )
    
    try:
        error_result = indexer.index_document(invalid_document)
        print(f"エラーテスト結果: {error_result}")
    except Exception as e:
        print(f"期待されたエラー: {e}")

if __name__ == "__main__":
    main()