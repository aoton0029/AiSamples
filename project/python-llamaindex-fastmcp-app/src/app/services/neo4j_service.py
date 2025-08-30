from neo4j import GraphDatabase
import os

class Neo4jService:
    def __init__(self):
        self.uri = os.getenv("NEO4J_HOST", "bolt://neo4j:7687")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record for record in result]

    def create_node(self, label, properties):
        query = f"CREATE (n:{label} $properties) RETURN n"
        return self.execute_query(query, {"properties": properties})

    def get_node(self, label, node_id):
        query = f"MATCH (n:{label}) WHERE id(n) = $id RETURN n"
        return self.execute_query(query, {"id": node_id})

    def update_node(self, node_id, properties):
        query = f"MATCH (n) WHERE id(n) = $id SET n += $properties RETURN n"
        return self.execute_query(query, {"id": node_id, "properties": properties})

    def delete_node(self, node_id):
        query = f"MATCH (n) WHERE id(n) = $id DELETE n"
        return self.execute_query(query, {"id": node_id})