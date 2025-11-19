"""
GLiNER-based classification service for detecting sensitive entities in prompts.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
import os
from pathlib import Path

from gliner import GLiNER


class EntityType(str, Enum):
    """Internal entity type categories"""
    PII = "pii"
    FINANCIAL = "financial"
    CONTRACT = "contract"
    IP = "ip"
    CUSTOM = "custom"


@dataclass
class DetectedEntity:
    """Represents a detected sensitive entity in text"""
    type: EntityType
    value: str
    start_index: int
    end_index: int
    confidence: float
    gliner_label: str  # Original GLiNER entity label


class ClassificationService:
    """
    Service for classifying prompts using GLiNER PII Edge model.
    Detects sensitive entities and provides confidence scores.
    """
    
    # GLiNER entity labels to internal entity type mapping
    ENTITY_TYPE_MAPPING = {
        # PII entities
        "person": EntityType.PII,
        "name": EntityType.PII,
        "email": EntityType.PII,
        "phone": EntityType.PII,
        "phone number": EntityType.PII,
        "address": EntityType.PII,
        "location": EntityType.PII,
        "date of birth": EntityType.PII,
        "ssn": EntityType.PII,
        "social security number": EntityType.PII,
        "passport": EntityType.PII,
        "driver license": EntityType.PII,
        "ip address": EntityType.PII,
        "medical": EntityType.PII,
        "health": EntityType.PII,
        
        # Financial entities
        "credit card": EntityType.FINANCIAL,
        "credit card number": EntityType.FINANCIAL,
        "account number": EntityType.FINANCIAL,
        "bank account": EntityType.FINANCIAL,
        "iban": EntityType.FINANCIAL,
        "routing number": EntityType.FINANCIAL,
        "amount": EntityType.FINANCIAL,
        "money": EntityType.FINANCIAL,
        "transaction": EntityType.FINANCIAL,
        
        # Contract/Legal entities
        "contract": EntityType.CONTRACT,
        "agreement": EntityType.CONTRACT,
        "legal": EntityType.CONTRACT,
        
        # Intellectual Property
        "patent": EntityType.IP,
        "trademark": EntityType.IP,
        "copyright": EntityType.IP,
        "trade secret": EntityType.IP,
    }
    
    # Entity labels to use with GLiNER model
    GLINER_LABELS = [
        "person", "email", "phone number", "address", "credit card number",
        "social security number", "date of birth", "passport", "driver license",
        "bank account", "ip address", "medical", "organization", "location"
    ]
    
    def __init__(self, model_name: str = "knowledgator/gliner-pii-edge-v1.0", cache_dir: Optional[str] = None):
        """
        Initialize the classification service with GLiNER model.
        
        Args:
            model_name: HuggingFace model identifier
            cache_dir: Directory to cache the model (defaults to ~/.cache/gliner)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.join(Path.home(), ".cache", "gliner")
        self.model: Optional[GLiNER] = None
        self._is_initialized = False
    
    def initialize(self) -> None:
        """
        Initialize and load the GLiNER model.
        Downloads the model on first run and caches it locally.
        """
        if self._is_initialized:
            return
        
        print(f"Loading GLiNER model: {self.model_name}")
        print(f"Cache directory: {self.cache_dir}")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load the model (will download if not cached)
        self.model = GLiNER.from_pretrained(self.model_name, cache_dir=self.cache_dir)
        
        self._is_initialized = True
        print("GLiNER model loaded successfully")
    
    def classify(self, text: str, threshold: float = 0.5) -> List[DetectedEntity]:
        """
        Classify text and detect sensitive entities using GLiNER.
        
        Args:
            text: The text to analyze
            threshold: Minimum confidence threshold for entity detection (0.0-1.0)
        
        Returns:
            List of detected entities with their types, positions, and confidence scores
        """
        if not self._is_initialized:
            raise RuntimeError("Classification service not initialized. Call initialize() first.")
        
        if not text or not text.strip():
            return []
        
        start_time = time.time()
        
        # Run GLiNER prediction
        entities = self.model.predict_entities(text, self.GLINER_LABELS, threshold=threshold)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Convert GLiNER entities to our internal format
        detected_entities = []
        for entity in entities:
            gliner_label = entity["label"].lower()
            entity_type = self._map_entity_type(gliner_label)
            
            detected_entity = DetectedEntity(
                type=entity_type,
                value=entity["text"],
                start_index=entity["start"],
                end_index=entity["end"],
                confidence=entity["score"],
                gliner_label=gliner_label
            )
            detected_entities.append(detected_entity)
        
        print(f"Classified text in {processing_time:.2f}ms, found {len(detected_entities)} entities")
        
        return detected_entities
    
    def _map_entity_type(self, gliner_label: str) -> EntityType:
        """
        Map GLiNER entity label to internal entity type.
        
        Args:
            gliner_label: The label returned by GLiNER
        
        Returns:
            Internal EntityType enum value
        """
        # Normalize the label
        normalized_label = gliner_label.lower().strip()
        
        # Try exact match first
        if normalized_label in self.ENTITY_TYPE_MAPPING:
            return self.ENTITY_TYPE_MAPPING[normalized_label]
        
        # Try partial matches for compound labels
        for key, entity_type in self.ENTITY_TYPE_MAPPING.items():
            if key in normalized_label or normalized_label in key:
                return entity_type
        
        # Default to PII for unknown entity types (conservative approach)
        return EntityType.PII
    
    def get_supported_labels(self) -> List[str]:
        """
        Get the list of entity labels supported by this classifier.
        
        Returns:
            List of supported entity label strings
        """
        return self.GLINER_LABELS.copy()
    
    def is_initialized(self) -> bool:
        """Check if the model is initialized and ready to use"""
        return self._is_initialized


# Global instance (singleton pattern)
_classification_service: Optional[ClassificationService] = None


def get_classification_service() -> ClassificationService:
    """
    Get or create the global classification service instance.
    
    Returns:
        Initialized ClassificationService instance
    """
    global _classification_service
    
    if _classification_service is None:
        _classification_service = ClassificationService()
        _classification_service.initialize()
    
    return _classification_service
