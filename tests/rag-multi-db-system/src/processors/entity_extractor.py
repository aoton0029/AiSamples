from typing import List, Dict, Any
import re

class EntityExtractor:
    """Extracts entities from documents such as names, organizations, and locations."""
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from the given text."""
        entities = []
        
        # Simple regex patterns for demonstration purposes
        patterns = {
            "PERSON": r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # Matches names like "John Doe"
            "ORGANIZATION": r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b(?: Inc\.| LLC| Corp\.)?',  # Matches organizations
            "LOCATION": r'\b(?:[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)+\b'  # Matches locations
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append({
                    "text": match,
                    "type": entity_type
                })
        
        return entities
    
    def extract_entities_from_documents(self, documents: List[str]) -> List[List[Dict[str, Any]]]:
        """Extract entities from a list of documents."""
        all_entities = []
        for doc in documents:
            entities = self.extract_entities(doc)
            all_entities.append(entities)
        return all_entities