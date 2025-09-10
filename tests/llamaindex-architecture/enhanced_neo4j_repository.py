import logging
from typing import List, Optional, Dict, Any
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core.schema import BaseNode, TextNode
from llama_index.tools.neo4j import Neo4jQueryTool
from llama_index.packs.neo4j_query_engine import Neo4jQueryEnginePack
from models import GraphRepository, Document, DocumentRelation
from config import db_config

logger = logging.getLogger(__name__)

class EnhancedNeo4jRepository(GraphRepository):
    """LlamaIndex Neo4j統合リポジトリ（機能強化版）"""
    
    def __init__(self):
        self.uri = db_config.NEO4J_URI
        self.user = db_config.NEO4J_USER
        self.password = db_config.NEO4J_PASSWORD
        self.graph_store = None
        self.query_tool = None
        self.query_engine_pack = None
    
    async def connect(self) -> bool:
        """Neo4jGraphStoreに接続"""
        try:
            # LlamaIndex Neo4jGraphStore初期化
            self.graph_store = Neo4jGraphStore(
                username=self.user,
                password=self.password,
                url=self.uri,
                database="neo4j"
            )
            
            # Neo4jQueryTool初期化
            self.query_tool = Neo4jQueryTool(
                neo4j_graph=self.graph_store,
                description="Neo4j database query tool for document relationships"
            )
            
            # Neo4jQueryEnginePack初期化
            self.query_engine_pack = Neo4jQueryEnginePack(
                username=self.user,
                password=self.password,
                url=self.uri,
                database="neo4j"
            )
            
            # 制約とインデックス作成
            await self._create_enhanced_constraints()
            
            logger.info(f"Connected to Neo4j at {self.uri} with enhanced features")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Neo4jから切断"""
        try:
            if self.graph_store:
                self.graph_store._driver.close()
            logger.info("Disconnected from Neo4j")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Neo4j: {e}")
            return False
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            if self.graph_store:
                # 簡単なクエリでヘルスチェック
                result = self.graph_store.query("RETURN 1 as test")
                return len(result) > 0
            return False
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
    
    async def _create_enhanced_constraints(self):
        """拡張制約とインデックス作成"""
        try:
            constraints_and_indexes = [
                # ドキュメントノード制約
                "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
                
                # インデックス作成
                "CREATE INDEX document_title_index IF NOT EXISTS FOR (d:Document) ON (d.title)",
                "CREATE INDEX document_file_type_index IF NOT EXISTS FOR (d:Document) ON (d.file_type)",
                "CREATE INDEX document_tags_index IF NOT EXISTS FOR (d:Document) ON (d.tags)",
                "CREATE INDEX chunk_content_index IF NOT EXISTS FOR (c:Chunk) ON (c.content)",
                
                # 関係性インデックス
                "CREATE INDEX relation_strength_index IF NOT EXISTS FOR ()-[r:SIMILAR]-() ON (r.strength)",
                "CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r:RELATED]-() ON (r.relation_type)",
                
                # フルテキストインデックス
                "CALL db.index.fulltext.createNodeIndex('documentContent', ['Document'], ['title', 'content']) ",
                "CALL db.index.fulltext.createNodeIndex('chunkContent', ['Chunk'], ['content']) "
            ]
            
            for constraint in constraints_and_indexes:
                try:
                    self.graph_store.query(constraint)
                except Exception as e:
                    # インデックスが既に存在する場合は無視
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Failed to create constraint/index: {e}")
            
            logger.info("Created enhanced Neo4j constraints and indexes")
            
        except Exception as e:
            logger.error(f"Failed to create enhanced constraints: {e}")
    
    async def create_document_node(self, document: Document) -> bool:
        """拡張ドキュメントノード作成"""
        try:
            # ドキュメントノード作成
            doc_query = """
            MERGE (d:Document {id: $id})
            SET d.title = $title,
                d.file_path = $file_path,
                d.file_type = $file_type,
                d.created_at = $created_at,
                d.updated_at = $updated_at,
                d.tags = $tags,
                d.content_length = $content_length,
                d.content_hash = $content_hash,
                d.content = $content
            """
            
            # コンテンツハッシュ生成
            import hashlib
            content_hash = hashlib.md5(document.content.encode()).hexdigest()
            
            self.graph_store.query(
                doc_query,
                param_map={
                    "id": document.id,
                    "title": document.title,
                    "file_path": document.file_path,
                    "file_type": document.file_type,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat(),
                    "tags": document.tags,
                    "content_length": len(document.content),
                    "content_hash": content_hash,
                    "content": document.content[:10000]  # 最初の10000文字のみ保存
                }
            )
            
            # タグノード作成と関係設定
            await self._create_tag_relationships(document)
            
            logger.info(f"Created enhanced document node: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create enhanced document node: {e}")
            return False
    
    async def _create_tag_relationships(self, document: Document):
        """タグとの関係作成"""
        try:
            for tag in document.tags:
                tag_query = """
                MERGE (t:Tag {name: $tag_name})
                WITH t
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:HAS_TAG]->(t)
                """
                
                self.graph_store.query(
                    tag_query,
                    param_map={
                        "tag_name": tag,
                        "doc_id": document.id
                    }
                )
        except Exception as e:
            logger.error(f"Failed to create tag relationships: {e}")
    
    async def create_enhanced_relation(self, relation: DocumentRelation, additional_context: Dict[str, Any] = None) -> bool:
        """拡張関係作成"""
        try:
            # 基本関係作成
            await self.create_relation(relation)
            
            # 追加コンテキスト情報があれば設定
            if additional_context:
                context_query = f"""
                MATCH (source:Document {{id: $source_id}})-[r:{relation.relation_type.upper()}]->(target:Document {{id: $target_id}})
                SET r += $context
                """
                
                self.graph_store.query(
                    context_query,
                    param_map={
                        "source_id": relation.source_doc_id,
                        "target_id": relation.target_doc_id,
                        "context": additional_context
                    }
                )
            
            logger.info(f"Created enhanced relation: {relation.source_doc_id} -> {relation.target_doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create enhanced relation: {e}")
            return False
    
    async def create_relation(self, relation: DocumentRelation) -> bool:
        """関係作成"""
        try:
            query = f"""
            MATCH (source:Document {{id: $source_id}})
            MATCH (target:Document {{id: $target_id}})
            MERGE (source)-[r:{relation.relation_type.upper()}]->(target)
            SET r.strength = $strength,
                r.created_at = datetime(),
                r.metadata = $metadata,
                r.relation_type = $relation_type
            """
            
            self.graph_store.query(
                query,
                param_map={
                    "source_id": relation.source_doc_id,
                    "target_id": relation.target_doc_id,
                    "strength": relation.strength,
                    "metadata": relation.metadata or {},
                    "relation_type": relation.relation_type
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create relation: {e}")
            return False
    
    async def find_related_documents(self, document_id: str, relation_types: List[str] = None) -> List[str]:
        """関連ドキュメント検索（拡張版）"""
        try:
            if relation_types:
                relation_filter = "|".join([rt.upper() for rt in relation_types])
                query = f"""
                MATCH (source:Document {{id: $document_id}})-[r:{relation_filter}]->(target:Document)
                RETURN target.id as document_id, r.strength as strength, type(r) as relation_type
                ORDER BY r.strength DESC
                LIMIT 20
                """
            else:
                query = """
                MATCH (source:Document {id: $document_id})-[r]->(target:Document)
                WHERE r.strength IS NOT NULL
                RETURN target.id as document_id, r.strength as strength, type(r) as relation_type
                ORDER BY r.strength DESC
                LIMIT 20
                """
            
            result = self.graph_store.query(query, param_map={"document_id": document_id})
            
            related_docs = [record["document_id"] for record in result]
            
            logger.info(f"Found {len(related_docs)} related documents for {document_id}")
            return related_docs
            
        except Exception as e:
            logger.error(f"Failed to find related documents: {e}")
            return []
    
    async def find_documents_by_tag(self, tag: str) -> List[str]:
        """タグによるドキュメント検索"""
        try:
            query = """
            MATCH (t:Tag {name: $tag})<-[:HAS_TAG]-(d:Document)
            RETURN d.id as document_id, d.title as title
            ORDER BY d.created_at DESC
            """
            
            result = self.graph_store.query(query, param_map={"tag": tag})
            return [record["document_id"] for record in result]
            
        except Exception as e:
            logger.error(f"Failed to find documents by tag: {e}")
            return []
    
    async def get_document_network(self, document_id: str, depth: int = 2) -> Dict[str, Any]:
        """ドキュメントネットワーク取得"""
        try:
            query = f"""
            MATCH path = (start:Document {{id: $document_id}})-[*1..{depth}]-(connected:Document)
            RETURN path
            LIMIT 100
            """
            
            result = self.graph_store.query(query, param_map={"document_id": document_id})
            
            # ネットワーク構造を構築
            nodes = set()
            edges = []
            
            for record in result:
                path = record["path"]
                # パス内のノードとエッジを抽出
                # (Neo4jのpath構造を解析)
                
            return {
                "nodes": list(nodes),
                "edges": edges,
                "center": document_id
            }
            
        except Exception as e:
            logger.error(f"Failed to get document network: {e}")
            return {"nodes": [], "edges": [], "center": document_id}
    
    async def natural_language_query(self, question: str) -> str:
        """自然言語クエリ実行"""
        try:
            if self.query_engine_pack:
                # Neo4jQueryEnginePackを使用した自然言語クエリ
                response = self.query_engine_pack.run(question)
                return str(response)
            else:
                return "Query engine not available"
                
        except Exception as e:
            logger.error(f"Failed to execute natural language query: {e}")
            return f"Error: {str(e)}"
    
    async def delete_document_node(self, document_id: str) -> bool:
        """ドキュメントノード削除"""
        try:
            query = """
            MATCH (d:Document {id: $document_id})
            DETACH DELETE d
            """
            
            self.graph_store.query(query, param_map={"document_id": document_id})
            
            logger.info(f"Deleted document node: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document node: {e}")
            return False
    
    async def get_enhanced_graph_stats(self) -> dict:
        """拡張グラフ統計取得"""
        try:
            stats_query = """
            CALL {
                MATCH (d:Document) RETURN count(d) as document_count
            }
            CALL {
                MATCH (t:Tag) RETURN count(t) as tag_count
            }
            CALL {
                MATCH ()-[r]->() RETURN count(r) as total_relationships
            }
            CALL {
                MATCH ()-[r:SIMILAR]->() RETURN count(r) as similar_relationships
            }
            CALL {
                MATCH ()-[r:RELATED]->() RETURN count(r) as related_relationships
            }
            RETURN document_count, tag_count, total_relationships, similar_relationships, related_relationships
            """
            
            result = self.graph_store.query(stats_query)
            
            if result:
                stats = result[0]
                return {
                    "total_documents": stats["document_count"],
                    "total_tags": stats["tag_count"],
                    "total_relationships": stats["total_relationships"],
                    "similar_relationships": stats["similar_relationships"],
                    "related_relationships": stats["related_relationships"]
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get enhanced graph stats: {e}")
            return {}