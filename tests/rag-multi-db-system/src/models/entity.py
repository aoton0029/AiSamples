from typing import Any, Dict

class Entity:
    """Entity model representing entities extracted from documents."""
    
    def __init__(self, entity_id: str, entity_type: str, properties: Dict[str, Any]):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.properties = properties

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary representation."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "properties": self.properties
        }