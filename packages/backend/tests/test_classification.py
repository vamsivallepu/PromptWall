"""
Unit tests for the GLiNER-based classification service.
"""
import pytest
from app.classification import ClassificationService, DetectedEntity, EntityType


@pytest.fixture
def classification_service():
    """Fixture to provide an initialized classification service"""
    service = ClassificationService()
    service.initialize()
    return service


class TestClassificationService:
    """Test suite for ClassificationService"""
    
    def test_initialization(self):
        """Test that the service initializes correctly"""
        service = ClassificationService()
        assert not service.is_initialized()
        
        service.initialize()
        assert service.is_initialized()
        assert service.model is not None
    
    def test_classify_empty_string(self, classification_service):
        """Test classification with empty string"""
        entities = classification_service.classify("")
        assert entities == []
    
    def test_classify_whitespace_only(self, classification_service):
        """Test classification with whitespace only"""
        entities = classification_service.classify("   \n\t  ")
        assert entities == []
    
    def test_classify_person_name(self, classification_service):
        """Test detection of person names"""
        text = "My name is John Smith and I work at Acme Corp."
        entities = classification_service.classify(text, threshold=0.3)
        
        # Should detect at least the person name
        assert len(entities) > 0
        
        # Check that we detected a PII entity
        pii_entities = [e for e in entities if e.type == EntityType.PII]
        assert len(pii_entities) > 0
    
    def test_classify_email(self, classification_service):
        """Test detection of email addresses"""
        text = "Contact me at john.doe@example.com for more information."
        entities = classification_service.classify(text, threshold=0.3)
        
        # Should detect at least one entity (email or person name)
        assert len(entities) > 0
        
        # All detected entities should be PII type
        for entity in entities:
            assert entity.type == EntityType.PII
    
    def test_classify_phone_number(self, classification_service):
        """Test detection of phone numbers"""
        text = "Call me at 555-123-4567 or (555) 987-6543."
        entities = classification_service.classify(text, threshold=0.3)
        
        # Should detect phone numbers
        assert len(entities) > 0
        
        # Check that detected entities are PII
        pii_entities = [e for e in entities if e.type == EntityType.PII]
        assert len(pii_entities) > 0
    
    def test_classify_multiple_entities(self, classification_service):
        """Test detection of multiple different entity types"""
        text = (
            "Hi, I'm Jane Doe. You can reach me at jane@company.com "
            "or call 555-0123. My SSN is 123-45-6789."
        )
        entities = classification_service.classify(text, threshold=0.3)
        
        # Should detect multiple entities
        assert len(entities) >= 2
        
        # All should be PII type
        for entity in entities:
            assert entity.type == EntityType.PII
            assert 0.0 <= entity.confidence <= 1.0
    
    def test_classify_no_sensitive_data(self, classification_service):
        """Test classification with no sensitive data"""
        text = "The weather is nice today. I like programming."
        entities = classification_service.classify(text)
        
        # Should detect no entities or very few with low confidence
        assert len(entities) <= 1
    
    def test_classify_very_long_text(self, classification_service):
        """Test classification with very long text (edge case)"""
        # Create a long text with some PII
        text = "Hello " * 2000 + "my name is John Smith and email is test@example.com " + "world " * 2000
        entities = classification_service.classify(text, threshold=0.3)
        
        # Very long text may be truncated by the model, so we just verify it doesn't crash
        # and returns a valid result (may be empty due to truncation)
        assert isinstance(entities, list)
    
    def test_classify_special_characters(self, classification_service):
        """Test classification with special characters"""
        text = "Email: test@example.com!!! Phone: (555) 123-4567??? Name: John@#$%"
        entities = classification_service.classify(text, threshold=0.3)
        
        # Should handle special characters and still detect entities
        assert len(entities) > 0
    
    def test_classify_confidence_threshold(self, classification_service):
        """Test that confidence threshold filtering works"""
        text = "Contact John Smith at john@example.com"
        
        # Low threshold should detect more
        entities_low = classification_service.classify(text, threshold=0.1)
        
        # High threshold should detect fewer
        entities_high = classification_service.classify(text, threshold=0.9)
        
        # Low threshold should have equal or more detections
        assert len(entities_low) >= len(entities_high)
    
    def test_entity_positions(self, classification_service):
        """Test that entity positions are correctly identified"""
        text = "Email: test@example.com"
        entities = classification_service.classify(text, threshold=0.3)
        
        if len(entities) > 0:
            entity = entities[0]
            # Check that positions are valid
            assert entity.start_index >= 0
            assert entity.end_index > entity.start_index
            assert entity.end_index <= len(text)
            
            # Check that the extracted text matches
            extracted = text[entity.start_index:entity.end_index]
            assert len(extracted) > 0
    
    def test_get_supported_labels(self, classification_service):
        """Test getting supported entity labels"""
        labels = classification_service.get_supported_labels()
        
        assert isinstance(labels, list)
        assert len(labels) > 0
        assert "email" in labels
        assert "person" in labels
    
    def test_entity_type_mapping(self, classification_service):
        """Test that entity types are correctly mapped"""
        # Test various entity type mappings
        assert classification_service._map_entity_type("person") == EntityType.PII
        assert classification_service._map_entity_type("email") == EntityType.PII
        assert classification_service._map_entity_type("credit card") == EntityType.FINANCIAL
        assert classification_service._map_entity_type("unknown_type") == EntityType.PII  # Default
    
    def test_classify_without_initialization(self):
        """Test that classify raises error if not initialized"""
        service = ClassificationService()
        
        with pytest.raises(RuntimeError, match="not initialized"):
            service.classify("test text")
