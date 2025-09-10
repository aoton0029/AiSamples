import logging
from typing import List, Optional
from neo4j import AsyncGraphDatabase
from models import GraphRepository, Document, DocumentRelation
from config import db_config

logger = logging.getLogger(__name__)

class Neo4jRepository(GraphRepository):
    """Neo4jグラフリポジトリ"""
    
    def __init__(self):
        self.uri = db_config.NEO4J_URI
        self.user = db_config.NEO4J_USER
        self.password = db_config.NEO4J_PASSWORD
        self.driver = None
    
    async def connect(self) -> bool:
        """Neo4jに接続"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # 接続確認
            await self.driver.verify_connectivity()
            
            # 制約とインデックス作成
            await self._create_constraints()
            
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Neo4jから切断"""
        try:
            if self.driver:
                await self.driver.close()
            logger.info("Disconnected from Neo4j")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Neo4j: {e}")
            return False
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            if self.driver:
                await self.driver.verify_connectivity()
                return True
            return False
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
    
    async def _create_constraints(self):
        """制約とインデックス作成"""
        try:
            async with self.driver.session() as session:
                # ドキュメントノードの一意制約
                await session.run(
                    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS "
                    "FOR (d:Document) REQUIRE d.id IS UNIQUE"
                )
                
                # インデックス作成
                await session.run(
                    "CREATE INDEX document_title_index IF NOT EXISTS "
                    "FOR (d:Document) ON (d.title)"
                )
                
                await session.run(
                    "CREATE INDEX document_file_type_index IF NOT EXISTS "
                    "FOR (d:Document) ON (d.file_type)"
                )
                
                logger.info("Created Neo4j constraints and indexes")
                
        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")
    
    async def create_document_node(self, document: Document) -> bool:
        """ドキュメントノード作成"""
        try:
            async with self.driver.session() as session:
                query = """
                MERGE (d:Document {id: $id})
                SET d.title = $title,
                    d.file_path = $file_path,
                    d.file_type = $file_type,
                    d.created_at = $created_at,
                    d.updated_at = $updated_at,
                    d.tags = $tags,
                    d.content_length = size($content)
                """
                
                await session.run(
                    query,
                    id=document.id,
                    title=document.title,
                    file_path=document.file_path,
                    file_type=document.file_type,
                    created_at=document.created_at.isoformat(),
                    updated_at=document.updated_at.isoformat(),
                    tags=document.tags,
                    content=document.content
                )
                
                logger.info(f"Created document node: {document.id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create document node: {e}")
            return False
    
    async def create_relation(self, relation: DocumentRelation) -> bool:
        """関係作成"""
        try:
            async with self.driver.session() as session:
                query = f"""
                MATCH (source:Document {{id: $source_id}})
                MATCH (target:Document {{id: $target_id}})
                MERGE (source)-[r:{relation.relation_type.upper()}]->(target)
                SET r.strength = $strength,
                    r.created_at = datetime(),
                    r.metadata = $metadata
                """
                
                await session.run(
                    query,
                    source_id=relation.source_doc_id,
                    target_id=relation.target_doc_id,
                    strength=relation.strength,
                    metadata=relation.metadata or {}
                )
                
                logger.info(f"Created relation: {relation.source_doc_id} -> {relation.target_doc_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create relation: {e}")
            return False
    
    async def find_related_documents(self, document_id: str, relation_types: List[str] = None) -> List[str]:
        """関連ドキュメント検索"""
        try:
            async with self.driver.session() as session:
                if relation_types:
                    # 特定の関係タイプのみ
                    relation_filter = "|".join([rt.upper() for rt in relation_types])
                    query = f"""
                    MATCH (source:Document {{id: $document_id}})-[r:{relation_filter}]->(target:Document)
                    RETURN target.id as document_id, r.strength as strength, type(r) as relation_type
                    ORDER BY r.strength DESC
                    """
                else:
                    # すべての関係タイプ
                    query = """
                    MATCH (source:Document {id: $document_id})-[r]->(target:Document)
                    RETURN target.id as document_id, r.strength as strength, type(r) as relation_type
                    ORDER BY r.strength DESC
                    """
                
                result = await session.run(query, document_id=document_id)
                
                related_docs = []
                async for record in result:
                    related_docs.append(record["document_id"])
                
                logger.info(f"Found {len(related_docs)} related documents for {document_id}")
                return related_docs
                
        except Exception as e:
            logger.error(f"Failed to find related documents: {e}")
            return []
    
    async def delete_document_node(self, document_id: str) -> bool:
        """ドキュメントノード削除"""
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (d:Document {id: $document_id})
                DETACH DELETE d
                """
                
                result = await session.run(query, document_id=document_id)
                
                logger.info(f"Deleted document node: {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete document node: {e}")
            return False
    
    async def get_document_relations(self, document_id: str) -> List[dict]:
        """ドキュメントの関係取得"""
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (source:Document {id: $document_id})-[r]->(target:Document)
                RETURN target.id as target_id, target.title as target_title, 
                       type(r) as relation_type, r.strength as strength, r.metadata as metadata
                UNION
                MATCH (source:Document)-[r]->(target:Document {id: $document_id})
                RETURN source.id as target_id, source.title as target_title, 
                       type(r) as relation_type, r.strength as strength, r.metadata as metadata
                """
                
                result = await session.run(query, document_id=document_id)
                
                relations = []
                async for record in result:
                    relations.append({
                        "target_id": record["target_id"],
                        "target_title": record["target_title"],
                        "relation_type": record["relation_type"],
                        "strength": record["strength"],
                        "metadata": record["metadata"]
                    })
                
                return relations
                
        except Exception as e:
            logger.error(f"Failed to get document relations: {e}")
            return []
    
    async def find_similar_documents(self, document_id: str, similarity_threshold: float = 0.7) -> List[str]:
        """類似ドキュメント検索"""
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (source:Document {id: $document_id})-[r:SIMILAR]->(target:Document)
                WHERE r.strength >= $threshold
                RETURN target.id as document_id, r.strength as strength
                ORDER BY r.strength DESC
                """
                
                result = await session.run(
                    query, 
                    document_id=document_id, 
                    threshold=similarity_threshold
                )
                
                similar_docs = []
                async for record in result:
                    similar_docs.append(record["document_id"])
                
                return similar_docs
                
        except Exception as e:
            logger.error(f"Failed to find similar documents: {e}")
            return []
    
    async def get_graph_stats(self) -> dict:
        """グラフ統計取得"""
        try:
            async with self.driver.session() as session:
                # ノード数取得
                node_result = await session.run("MATCH (d:Document) RETURN count(d) as node_count")
                node_count = 0
                async for record in node_result:
                    node_count = record["node_count"]
                
                # 関係数取得
                rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = 0
                async for record in rel_result:
                    rel_count = record["rel_count"]
                
                # 関係タイプ別統計
                rel_type_result = await session.run(
                    "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count"
                )
                rel_type_stats = {}
                async for record in rel_type_result:
                    rel_type_stats[record["rel_type"]] = record["count"]
                
                return {
                    "total_nodes": node_count,
                    "total_relationships": rel_count,
                    "relationship_types": rel_type_stats
                }
                
        except Exception as e:
            logger.error(f"Failed to get graph stats: {e}")
            return {}