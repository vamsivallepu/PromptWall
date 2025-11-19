"""
Unit tests for the sanitization engine.
Tests placeholder replacement, masking, redaction strategies, and diff generation.
"""
import pytest
from app.sanitization import (
    SanitizationEngine,
    SanitizationStrategy,
    SanitizationResult,
    Replacement,
    DiffResult,
    DiffSpan
)
from app.classification import DetectedEntity, EntityType


class TestSanitizationEngine:
    """Test suite for SanitizationEngine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SanitizationEngine()
    
    def test_sanitize_empty_prompt(self):
        """Test sanitization with empty prompt"""
        result = self.engine.sanitize("", [])
        
        assert result.sanitized_prompt == ""
        assert result.replacements == []
        assert result.is_fully_sanitized is True
    
    def test_sanitize_no_entities(self):
        """Test sanitization with no detected entities"""
        prompt = "This is a clean prompt with no sensitive data."
        result = self.engine.sanitize(prompt, [])
        
        assert result.sanitized_prompt == prompt
        assert result.replacements == []
        assert result.is_fully_sanitized is True
    
    def test_sanitize_single_email(self):
        """Test sanitization with a single email address"""
        prompt = "Contact me at john.doe@example.com for details."
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="john.doe@example.com",
                start_index=14,
                end_index=34,  # Correct end index without trailing space
                confidence=0.95,
                gliner_label="email"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities)
        
        assert result.sanitized_prompt == "Contact me at [EMAIL] for details."
        assert len(result.replacements) == 1
        assert result.replacements[0].original == "john.doe@example.com"
        assert result.replacements[0].placeholder == "[EMAIL]"
        assert result.replacements[0].type == "email"
        assert result.is_fully_sanitized is True
    
    def test_sanitize_multiple_entities(self):
        """Test sanitization with multiple entities"""
        prompt = "John Smith's email is john@example.com and phone is 555-1234."
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="John Smith",
                start_index=0,
                end_index=10,
                confidence=0.92,
                gliner_label="person"
            ),
            DetectedEntity(
                type=EntityType.PII,
                value="john@example.com",
                start_index=22,
                end_index=38,  # Fixed index
                confidence=0.95,
                gliner_label="email"
            ),
            DetectedEntity(
                type=EntityType.PII,
                value="555-1234",
                start_index=52,  # Fixed index
                end_index=60,    # Fixed index
                confidence=0.88,
                gliner_label="phone number"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities)
        
        expected = "[PERSON]'s email is [EMAIL] and phone is [PHONE]."
        assert result.sanitized_prompt == expected
        assert len(result.replacements) == 3
        assert result.is_fully_sanitized is True
    
    def test_sanitize_credit_card(self):
        """Test sanitization with credit card number"""
        prompt = "My card number is 4532-1234-5678-9010."
        entities = [
            DetectedEntity(
                type=EntityType.FINANCIAL,
                value="4532-1234-5678-9010",
                start_index=18,
                end_index=37,
                confidence=0.97,
                gliner_label="credit card number"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities)
        
        assert result.sanitized_prompt == "My card number is [CREDIT_CARD]."
        assert result.replacements[0].placeholder == "[CREDIT_CARD]"
    
    def test_sanitize_ssn(self):
        """Test sanitization with SSN"""
        prompt = "SSN: 123-45-6789"
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="123-45-6789",
                start_index=5,
                end_index=16,
                confidence=0.93,
                gliner_label="ssn"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities)
        
        assert result.sanitized_prompt == "SSN: [SSN]"
        assert result.replacements[0].placeholder == "[SSN]"
    
    def test_sanitize_with_mask_strategy(self):
        """Test sanitization using mask strategy"""
        prompt = "Email: john.doe@example.com"
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="john.doe@example.com",
                start_index=7,
                end_index=28,
                confidence=0.95,
                gliner_label="email"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities, strategy=SanitizationStrategy.MASK)
        
        # Email should be masked as j***e@example.com
        assert "***" in result.sanitized_prompt
        assert "@example.com" in result.sanitized_prompt
        assert result.replacements[0].placeholder.startswith("j***")
    
    def test_sanitize_with_mask_strategy_phone(self):
        """Test masking strategy with phone number"""
        prompt = "Call 555-123-4567"
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="555-123-4567",
                start_index=5,
                end_index=17,
                confidence=0.90,
                gliner_label="phone number"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities, strategy=SanitizationStrategy.MASK)
        
        # Phone should show last 4 digits
        assert result.sanitized_prompt == "Call ***-**-4567"
    
    def test_sanitize_with_redact_strategy(self):
        """Test sanitization using redact strategy"""
        prompt = "My email is john@example.com and that's it."
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="john@example.com",
                start_index=12,
                end_index=28,  # Fixed index
                confidence=0.95,
                gliner_label="email"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities, strategy=SanitizationStrategy.REDACT)
        
        # Redaction removes the entity completely
        assert result.sanitized_prompt == "My email is  and that's it."
        assert result.replacements[0].placeholder == ""
    
    def test_sanitize_preserves_whitespace(self):
        """Test that sanitization preserves prompt structure and whitespace"""
        prompt = "Name:  John Doe  \nEmail:  john@example.com"
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="John Doe",
                start_index=7,
                end_index=15,
                confidence=0.92,
                gliner_label="person"
            ),
            DetectedEntity(
                type=EntityType.PII,
                value="john@example.com",
                start_index=26,
                end_index=42,
                confidence=0.95,
                gliner_label="email"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities)
        
        # Check that whitespace is preserved
        assert "  " in result.sanitized_prompt
        assert "\n" in result.sanitized_prompt
        assert result.sanitized_prompt == "Name:  [PERSON]  \nEmail:  [EMAIL]"
    
    def test_sanitize_adjacent_entities(self):
        """Test sanitization with adjacent entities"""
        prompt = "John Smith john@example.com"
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="John Smith",
                start_index=0,
                end_index=10,
                confidence=0.92,
                gliner_label="person"
            ),
            DetectedEntity(
                type=EntityType.PII,
                value="john@example.com",
                start_index=11,
                end_index=27,
                confidence=0.95,
                gliner_label="email"
            )
        ]
        
        result = self.engine.sanitize(prompt, entities)
        
        assert result.sanitized_prompt == "[PERSON] [EMAIL]"
        assert len(result.replacements) == 2


class TestDiffGeneration:
    """Test suite for diff generation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SanitizationEngine()
    
    def test_generate_diff_no_changes(self):
        """Test diff generation with no changes"""
        original = "This is a clean prompt."
        sanitized = "This is a clean prompt."
        
        diff = self.engine.generate_diff(original, sanitized, [])
        
        assert diff.original == original
        assert diff.sanitized == sanitized
        assert diff.num_changes == 0
        assert len(diff.spans) == 1
        assert diff.spans[0].is_changed is False
        assert diff.spans[0].text == original
    
    def test_generate_diff_single_replacement(self):
        """Test diff generation with single replacement"""
        original = "Contact john@example.com"
        sanitized = "Contact [EMAIL]"
        replacements = [
            Replacement(
                original="john@example.com",
                placeholder="[EMAIL]",
                type="email",
                start_index=8,
                end_index=24
            )
        ]
        
        diff = self.engine.generate_diff(original, sanitized, replacements)
        
        assert diff.num_changes == 1
        assert len(diff.spans) == 2
        
        # First span: unchanged text
        assert diff.spans[0].text == "Contact "
        assert diff.spans[0].is_changed is False
        
        # Second span: changed text
        assert diff.spans[1].text == "john@example.com"
        assert diff.spans[1].is_changed is True
        assert diff.spans[1].entity_type == "email"
    
    def test_generate_diff_multiple_replacements(self):
        """Test diff generation with multiple replacements"""
        original = "John Smith at john@example.com or 555-1234"
        sanitized = "[PERSON] at [EMAIL] or [PHONE]"
        replacements = [
            Replacement(
                original="John Smith",
                placeholder="[PERSON]",
                type="person",
                start_index=0,
                end_index=10
            ),
            Replacement(
                original="john@example.com",
                placeholder="[EMAIL]",
                type="email",
                start_index=14,
                end_index=30
            ),
            Replacement(
                original="555-1234",
                placeholder="[PHONE]",
                type="phone number",
                start_index=34,
                end_index=42
            )
        ]
        
        diff = self.engine.generate_diff(original, sanitized, replacements)
        
        assert diff.num_changes == 3
        assert len(diff.spans) == 5  # 3 changed + 2 unchanged
        
        # Check changed spans
        changed_spans = [s for s in diff.spans if s.is_changed]
        assert len(changed_spans) == 3
        assert changed_spans[0].text == "John Smith"
        assert changed_spans[1].text == "john@example.com"
        assert changed_spans[2].text == "555-1234"
    
    def test_generate_diff_at_start(self):
        """Test diff generation with replacement at start"""
        original = "john@example.com is my email"
        sanitized = "[EMAIL] is my email"
        replacements = [
            Replacement(
                original="john@example.com",
                placeholder="[EMAIL]",
                type="email",
                start_index=0,
                end_index=16
            )
        ]
        
        diff = self.engine.generate_diff(original, sanitized, replacements)
        
        assert len(diff.spans) == 2
        assert diff.spans[0].is_changed is True
        assert diff.spans[0].text == "john@example.com"
        assert diff.spans[1].is_changed is False
        assert diff.spans[1].text == " is my email"
    
    def test_generate_diff_at_end(self):
        """Test diff generation with replacement at end"""
        original = "Email me at john@example.com"
        sanitized = "Email me at [EMAIL]"
        replacements = [
            Replacement(
                original="john@example.com",
                placeholder="[EMAIL]",
                type="email",
                start_index=12,
                end_index=28
            )
        ]
        
        diff = self.engine.generate_diff(original, sanitized, replacements)
        
        assert len(diff.spans) == 2
        assert diff.spans[0].is_changed is False
        assert diff.spans[0].text == "Email me at "
        assert diff.spans[1].is_changed is True
        assert diff.spans[1].text == "john@example.com"
    
    def test_format_diff_text(self):
        """Test formatting diff as human-readable text"""
        original = "Contact john@example.com"
        sanitized = "Contact [EMAIL]"
        replacements = [
            Replacement(
                original="john@example.com",
                placeholder="[EMAIL]",
                type="email",
                start_index=8,
                end_index=24
            )
        ]
        
        diff = self.engine.generate_diff(original, sanitized, replacements)
        formatted = self.engine.format_diff_text(diff)
        
        assert "=== ORIGINAL ===" in formatted
        assert "=== SANITIZED ===" in formatted
        assert "=== SUMMARY ===" in formatted
        assert "john@example.com" in formatted
        assert "[EMAIL]" in formatted
        assert "Total changes: 1" in formatted


class TestPlaceholderMapping:
    """Test suite for placeholder mapping"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SanitizationEngine()
    
    def test_placeholder_for_person(self):
        """Test placeholder for person entity"""
        entity = DetectedEntity(
            type=EntityType.PII,
            value="John Doe",
            start_index=0,
            end_index=8,
            confidence=0.9,
            gliner_label="person"
        )
        
        placeholder = self.engine._get_placeholder(entity)
        assert placeholder == "[PERSON]"
    
    def test_placeholder_for_email(self):
        """Test placeholder for email entity"""
        entity = DetectedEntity(
            type=EntityType.PII,
            value="test@example.com",
            start_index=0,
            end_index=16,
            confidence=0.95,
            gliner_label="email"
        )
        
        placeholder = self.engine._get_placeholder(entity)
        assert placeholder == "[EMAIL]"
    
    def test_placeholder_for_credit_card(self):
        """Test placeholder for credit card entity"""
        entity = DetectedEntity(
            type=EntityType.FINANCIAL,
            value="4532123456789010",
            start_index=0,
            end_index=16,
            confidence=0.97,
            gliner_label="credit card number"
        )
        
        placeholder = self.engine._get_placeholder(entity)
        assert placeholder == "[CREDIT_CARD]"
    
    def test_placeholder_for_unknown_entity(self):
        """Test placeholder for unknown entity type"""
        entity = DetectedEntity(
            type=EntityType.CUSTOM,
            value="sensitive",
            start_index=0,
            end_index=9,
            confidence=0.8,
            gliner_label="unknown"
        )
        
        placeholder = self.engine._get_placeholder(entity)
        assert placeholder == "[CUSTOM]"


class TestMaskingStrategy:
    """Test suite for masking strategy"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SanitizationEngine()
    
    def test_mask_short_value(self):
        """Test masking very short values"""
        masked = self.engine._mask_value("ab")
        assert masked == "***"
    
    def test_mask_email(self):
        """Test masking email addresses"""
        masked = self.engine._mask_value("john.doe@example.com")
        assert "@example.com" in masked
        assert "***" in masked
        assert masked.startswith("j***")
    
    def test_mask_short_email(self):
        """Test masking short email addresses"""
        masked = self.engine._mask_value("ab@example.com")
        assert masked == "***@example.com"
    
    def test_mask_phone_number(self):
        """Test masking phone numbers"""
        masked = self.engine._mask_value("555-123-4567")
        assert masked == "***-**-4567"
    
    def test_mask_short_phone(self):
        """Test masking short phone numbers"""
        masked = self.engine._mask_value("5551")
        assert masked == "***1"
    
    def test_mask_generic_value(self):
        """Test masking generic values"""
        masked = self.engine._mask_value("SensitiveData")
        assert masked == "S***a"
    
    def test_mask_empty_value(self):
        """Test masking empty value"""
        masked = self.engine._mask_value("")
        assert masked == "***"
