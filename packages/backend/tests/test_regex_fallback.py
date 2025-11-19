"""
Unit tests for regex-based fallback classifier.
"""
import pytest
from app.regex_fallback import (
    RegexFallbackClassifier,
    merge_entities,
    get_regex_classifier
)
from app.classification import DetectedEntity, EntityType


class TestRegexFallbackClassifier:
    """Test suite for RegexFallbackClassifier"""
    
    @pytest.fixture
    def classifier(self):
        """Fixture to provide a regex classifier"""
        return RegexFallbackClassifier()
    
    def test_classify_email(self, classifier):
        """Test email detection"""
        text = "Contact me at john.doe@example.com for details."
        entities = classifier.classify(text)
        
        # Should detect email
        assert len(entities) > 0
        email_entities = [e for e in entities if "email" in e.gliner_label]
        assert len(email_entities) == 1
        assert email_entities[0].type == EntityType.PII
        assert "john.doe@example.com" in email_entities[0].value
    
    def test_classify_multiple_emails(self, classifier):
        """Test detection of multiple emails"""
        text = "Email john@example.com or jane@company.org"
        entities = classifier.classify(text)
        
        email_entities = [e for e in entities if "email" in e.gliner_label]
        assert len(email_entities) == 2
    
    def test_classify_phone_us_format(self, classifier):
        """Test US phone number detection"""
        text = "Call me at (555) 123-4567 or 555-987-6543"
        entities = classifier.classify(text)
        
        phone_entities = [e for e in entities if "phone" in e.gliner_label]
        assert len(phone_entities) >= 2
        
        for entity in phone_entities:
            assert entity.type == EntityType.PII
    
    def test_classify_phone_international(self, classifier):
        """Test international phone number detection"""
        text = "International: +1 555 123 4567 or +44 20 1234 5678"
        entities = classifier.classify(text)
        
        phone_entities = [e for e in entities if "phone" in e.gliner_label]
        assert len(phone_entities) >= 1
    
    def test_classify_credit_card(self, classifier):
        """Test credit card detection"""
        # Visa format
        text = "Card number: 4532123456789010"
        entities = classifier.classify(text)
        
        cc_entities = [e for e in entities if "credit_card" in e.gliner_label]
        assert len(cc_entities) >= 1
        assert cc_entities[0].type == EntityType.FINANCIAL
    
    def test_classify_credit_card_formatted(self, classifier):
        """Test formatted credit card detection"""
        text = "Card: 4532-1234-5678-9010"
        entities = classifier.classify(text)
        
        cc_entities = [e for e in entities if "credit_card" in e.gliner_label]
        assert len(cc_entities) >= 1
    
    def test_classify_ssn(self, classifier):
        """Test SSN detection"""
        text = "SSN: 123-45-6789"
        entities = classifier.classify(text)
        
        ssn_entities = [e for e in entities if "ssn" in e.gliner_label]
        assert len(ssn_entities) == 1
        assert ssn_entities[0].type == EntityType.PII
    
    def test_classify_ssn_no_dashes(self, classifier):
        """Test SSN detection without dashes"""
        text = "SSN: 123456789"
        entities = classifier.classify(text)
        
        ssn_entities = [e for e in entities if "ssn" in e.gliner_label]
        assert len(ssn_entities) == 1
    
    def test_classify_ip_address(self, classifier):
        """Test IP address detection"""
        text = "Server IP: 192.168.1.100"
        entities = classifier.classify(text)
        
        ip_entities = [e for e in entities if "ip_address" in e.gliner_label]
        assert len(ip_entities) == 1
        assert ip_entities[0].type == EntityType.PII
    
    def test_classify_iban(self, classifier):
        """Test IBAN detection"""
        text = "IBAN: GB82WEST12345698765432"
        entities = classifier.classify(text)
        
        iban_entities = [e for e in entities if "iban" in e.gliner_label]
        assert len(iban_entities) == 1
        assert iban_entities[0].type == EntityType.FINANCIAL
    
    def test_classify_empty_string(self, classifier):
        """Test with empty string"""
        entities = classifier.classify("")
        assert entities == []
    
    def test_classify_no_sensitive_data(self, classifier):
        """Test with text containing no sensitive data"""
        text = "The weather is nice today."
        entities = classifier.classify(text)
        assert len(entities) == 0
    
    def test_classify_special_characters(self, classifier):
        """Test handling of special characters"""
        text = "Email: test@example.com!!! Phone: (555) 123-4567???"
        entities = classifier.classify(text)
        
        # Should still detect entities despite special characters
        assert len(entities) >= 2
    
    def test_entity_positions(self, classifier):
        """Test that entity positions are correct"""
        text = "Email: test@example.com"
        entities = classifier.classify(text)
        
        assert len(entities) > 0
        entity = entities[0]
        
        # Verify positions
        assert entity.start_index >= 0
        assert entity.end_index > entity.start_index
        assert entity.end_index <= len(text)
        
        # Verify extracted text
        extracted = text[entity.start_index:entity.end_index]
        assert "@" in extracted
    
    def test_add_custom_pattern(self, classifier):
        """Test adding custom regex patterns"""
        # Add custom pattern for employee IDs
        classifier.add_custom_pattern(
            name="employee_id",
            pattern=r"EMP-\d{6}",
            entity_type=EntityType.CUSTOM,
            confidence=0.9
        )
        
        text = "Employee ID: EMP-123456"
        entities = classifier.classify(text)
        
        custom_entities = [e for e in entities if e.gliner_label == "employee_id"]
        assert len(custom_entities) == 1
        assert custom_entities[0].type == EntityType.CUSTOM
        assert custom_entities[0].confidence == 0.9
    
    def test_add_invalid_pattern(self, classifier):
        """Test that invalid regex patterns raise errors"""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            classifier.add_custom_pattern(
                name="invalid",
                pattern="[invalid(regex",
                entity_type=EntityType.CUSTOM
            )
    
    def test_confidence_scores(self, classifier):
        """Test that confidence scores are within valid range"""
        text = "Email: test@example.com, Phone: 555-1234"
        entities = classifier.classify(text)
        
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0


class TestMergeEntities:
    """Test suite for entity merging functionality"""
    
    def test_merge_no_overlap(self):
        """Test merging entities with no overlap"""
        gliner_entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.9, "person")
        ]
        regex_entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 10, 26, 0.95, "email")
        ]
        
        merged = merge_entities(gliner_entities, regex_entities)
        
        assert len(merged) == 2
    
    def test_merge_with_overlap(self):
        """Test merging entities with overlap (deduplication)"""
        gliner_entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 10, 26, 0.85, "email")
        ]
        regex_entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 10, 26, 0.95, "email")
        ]
        
        merged = merge_entities(gliner_entities, regex_entities)
        
        # Should deduplicate - only keep GLiNER detection
        assert len(merged) == 1
    
    def test_merge_partial_overlap(self):
        """Test merging with partial overlap"""
        gliner_entities = [
            DetectedEntity(EntityType.PII, "John Smith", 0, 10, 0.9, "person")
        ]
        regex_entities = [
            DetectedEntity(EntityType.PII, "Smith", 5, 10, 0.8, "name")
        ]
        
        merged = merge_entities(gliner_entities, regex_entities)
        
        # Should deduplicate due to significant overlap
        assert len(merged) == 1
    
    def test_merge_empty_gliner(self):
        """Test merging when GLiNER entities are empty"""
        regex_entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 10, 26, 0.95, "email")
        ]
        
        merged = merge_entities([], regex_entities)
        
        assert len(merged) == 1
        assert merged == regex_entities
    
    def test_merge_empty_regex(self):
        """Test merging when regex entities are empty"""
        gliner_entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.9, "person")
        ]
        
        merged = merge_entities(gliner_entities, [])
        
        assert len(merged) == 1
        assert merged == gliner_entities
    
    def test_merge_sorting(self):
        """Test that merged entities are sorted by position"""
        gliner_entities = [
            DetectedEntity(EntityType.PII, "Jane", 20, 24, 0.9, "person")
        ]
        regex_entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 5, 21, 0.95, "email")
        ]
        
        merged = merge_entities(gliner_entities, regex_entities)
        
        # Should be sorted by start_index
        assert merged[0].start_index < merged[1].start_index
    
    def test_merge_multiple_entities(self):
        """Test merging multiple entities from both sources"""
        gliner_entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.9, "person"),
            DetectedEntity(EntityType.PII, "Jane", 20, 24, 0.85, "person")
        ]
        regex_entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 10, 26, 0.95, "email"),
            DetectedEntity(EntityType.PII, "555-1234", 30, 38, 0.9, "phone")
        ]
        
        merged = merge_entities(gliner_entities, regex_entities)
        
        # Jane overlaps with email, so should have 3 total
        assert len(merged) >= 3


class TestGetRegexClassifier:
    """Test the global classifier singleton"""
    
    def test_singleton_pattern(self):
        """Test that get_regex_classifier returns the same instance"""
        classifier1 = get_regex_classifier()
        classifier2 = get_regex_classifier()
        
        assert classifier1 is classifier2
