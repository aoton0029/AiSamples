from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Document:
    """ドキュメントデータクラス"""
    id: str
    title: str
    content: str
    file_path: str
    file_type: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class DocumentChunk:
    """ドキュメントチャンクデータクラス"""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.document_id}_chunk_{self.chunk_index}"

@dataclass
class SearchResult:
    """検索結果データクラス"""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    document_title: str

@dataclass
class DocumentRelation:
    """ドキュメント関係データクラス"""
    source_doc_id: str
    target_doc_id: str
    relation_type: str  # "similar", "references", "contains", etc.
    strength: float
    metadata: Dict[str, Any] = None

class BaseRepository(ABC):
    """ベースリポジトリインターフェース"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """データベースに接続"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """データベースから切断"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass

class VectorRepository(BaseRepository):
    """ベクトル検索リポジトリインターフェース"""
    
    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """コレクション作成"""
        pass
    
    @abstractmethod
    async def insert_vectors(self, chunks: List[DocumentChunk]) -> bool:
        """ベクトル挿入"""
        pass
    
    @abstractmethod
    async def search_vectors(self, query_vector: List[float], top_k: int) -> List[SearchResult]:
        """ベクトル検索"""
        pass
    
    @abstractmethod
    async def delete_vectors(self, document_id: str) -> bool:
        """ベクトル削除"""
        pass

class DocumentRepository(BaseRepository):
    """ドキュメントリポジトリインターフェース"""
    
    @abstractmethod
    async def save_document(self, document: Document) -> str:
        """ドキュメント保存"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """ドキュメント取得"""
        pass
    
    @abstractmethod
    async def search_documents(self, query: Dict[str, Any]) -> List[Document]:
        """ドキュメント検索"""
        pass
    
    @abstractmethod
    async def update_document(self, document: Document) -> bool:
        """ドキュメント更新"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """ドキュメント削除"""
        pass

class GraphRepository(BaseRepository):
    """グラフデータベースリポジトリインターフェース"""
    
    @abstractmethod
    async def create_document_node(self, document: Document) -> bool:
        """ドキュメントノード作成"""
        pass
    
    @abstractmethod
    async def create_relation(self, relation: DocumentRelation) -> bool:
        """関係作成"""
        pass
    
    @abstractmethod
    async def find_related_documents(self, document_id: str, relation_types: List[str] = None) -> List[str]:
        """関連ドキュメント検索"""
        pass
    
    @abstractmethod
    async def delete_document_node(self, document_id: str) -> bool:
        """ドキュメントノード削除"""
        pass

class CacheRepository(BaseRepository):
    """キャッシュリポジトリインターフェース"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expire_time: int = None) -> bool:
        """キャッシュ設定"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """キャッシュ削除"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """キャッシュ存在確認"""
        pass