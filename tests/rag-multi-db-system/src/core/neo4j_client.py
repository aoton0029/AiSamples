from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional


class Neo4jClient:
    """Neo4jを使用したグラフDB操作クラス"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        """接続を閉じる"""
        self.driver.close()
        
    def create_document_node(self, document_id: str, title: str, metadata: Dict[str, Any]) -> bool:
        """ドキュメントノードを作成"""
        query = """
        CREATE (d:Document {
            document_id: $document_id,
            title: $title,
            created_at: datetime(),
            metadata: $metadata
        })
        """
        try:
            with self.driver.session() as session:
                session.run(query, document_id=document_id, title=title, metadata=metadata)
            return True
        except Exception as e:
            print(f"ドキュメントノード作成エラー: {e}")
            return False
    
    def create_entity_node(self, entity_id: str, entity_type: str, properties: Dict[str, Any]) -> bool:
        """エンティティノードを作成"""
        query = f"""
        CREATE (e:{entity_type} {{
            entity_id: $entity_id,
            properties: $properties,
            created_at: datetime()
        }})
        """
        try:
            with self.driver.session() as session:
                session.run(query, entity_id=entity_id, properties=properties)
            return True
        except Exception as e:
            print(f"エンティティノード作成エラー: {e}")
            return False
    
    def create_relationship(self, from_node_id: str, to_node_id: str, 
                          relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """ノード間の関係を作成"""
        query = """
        MATCH (a {entity_id: $from_id}), (b {entity_id: $to_id})
        CREATE (a)-[r:""" + relationship_type + """ $properties]->(b)
        """
        try:
            with self.driver.session() as session:
                session.run(query, from_id=from_node_id, to_id=to_node_id, 
                          properties=properties or {})
            return True
        except Exception as e:
            print(f"関係作成エラー: {e}")
            return False
    
    def find_related_documents(self, entity_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """エンティティに関連するドキュメントを検索"""
        query = """
        MATCH path = (e {entity_id: $entity_id})-[*1..""" + str(max_depth) + """]->(d:Document)
        RETURN d.document_id as document_id, d.title as title, d.metadata as metadata,
               length(path) as distance
        ORDER BY distance
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, entity_id=entity_id)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"関連ドキュメント検索エラー: {e}")
            return []
    
    def find_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """エンティティの関係を検索"""
        query = """
        MATCH (e {entity_id: $entity_id})-[r]-(other)
        RETURN type(r) as relationship_type, 
               other.entity_id as related_entity_id,
               labels(other) as related_entity_type,
               r as relationship_properties
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, entity_id=entity_id)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"エンティティ関係検索エラー: {e}")
            return []
    
    def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """ドキュメントに含まれるエンティティを取得"""
        query = """
        MATCH (d:Document {document_id: $document_id})-[r]-(e)
        WHERE NOT e:Document
        RETURN e.entity_id as entity_id, labels(e) as entity_type, e.properties as properties
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, document_id=document_id)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"ドキュメントエンティティ検索エラー: {e}")
            return []
    
    def delete_document_graph(self, document_id: str) -> bool:
        """ドキュメントとその関係を削除"""
        query = """
        MATCH (d:Document {document_id: $document_id})
        DETACH DELETE d
        """
        try:
            with self.driver.session() as session:
                session.run(query, document_id=document_id)
            return True
        except Exception as e:
            print(f"ドキュメントグラフ削除エラー: {e}")
            return False