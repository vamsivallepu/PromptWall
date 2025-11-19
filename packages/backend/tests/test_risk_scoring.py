"""
Unit tests for the risk scoring algorithm.
"""
import pytest
from app.risk_scoring import RiskScoringEngine, RiskLevel
from app.classification import DetectedEntity, EntityType


class TestRiskScoringEngine:
    """Test suite for RiskScoringEngine"""
    
    @pytest.fixture
    def engine(self):
        """Fixture to provide a risk scoring engine"""
        return RiskScoringEngine()
    
    def test_empty_entities_green(self, engine):
        """Test that no entities results in GREEN risk level"""
        score = engine.score([], prompt_length=100)
        
        assert score.risk_level == RiskLevel.GREEN
        assert score.entity_count == 0
        assert score.high_confidence_count == 0
        assert score.max_confidence == 0.0
    
    def test_single_low_confidence_entity_amber(self, engine):
        """Test that single low-confidence entity results in AMBER"""
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="John",
                start_index=0,
                end_index=4,
                confidence=0.5,
                gliner_label="person"
            )
        ]
        
        score = engine.score(entities, prompt_length=50)
        
        assert score.risk_level == RiskLevel.AMBER
        assert score.entity_count == 1
        assert score.high_confidence_count == 0
    
    def test_single_high_confidence_pii_red(self, engine):
        """Test that high-confidence PII results in RED"""
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="john@example.com",
                start_index=0,
                end_index=16,
                confidence=0.95,
                gliner_label="email"
            )
        ]
        
        score = engine.score(entities, prompt_length=50)
        
        assert score.risk_level == RiskLevel.RED
        assert score.entity_count == 1
        assert score.high_confidence_count == 1
        assert score.max_confidence == 0.95
    
    def test_multiple_entities_amber(self, engine):
        """Test that 2-3 entities result in AMBER"""
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="John",
                start_index=0,
                end_index=4,
                confidence=0.6,
                gliner_label="person"
            ),
            DetectedEntity(
                type=EntityType.PII,
                value="555-1234",
                start_index=10,
                end_index=18,
                confidence=0.65,
                gliner_label="phone"
            )
        ]
        
        score = engine.score(entities, prompt_length=50)
        
        assert score.risk_level == RiskLevel.AMBER
        assert score.entity_count == 2
    
    def test_many_entities_red(self, engine):
        """Test that 4+ entities result in RED"""
        entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.6, "person"),
            DetectedEntity(EntityType.PII, "jane@example.com", 10, 26, 0.8, "email"),
            DetectedEntity(EntityType.PII, "555-1234", 30, 38, 0.7, "phone"),
            DetectedEntity(EntityType.PII, "123 Main St", 40, 51, 0.6, "address"),
        ]
        
        score = engine.score(entities, prompt_length=100)
        
        assert score.risk_level == RiskLevel.RED
        assert score.entity_count == 4
    
    def test_high_confidence_financial_red(self, engine):
        """Test that high-confidence financial data results in RED"""
        entities = [
            DetectedEntity(
                type=EntityType.FINANCIAL,
                value="4532-1234-5678-9010",
                start_index=0,
                end_index=19,
                confidence=0.92,
                gliner_label="credit_card"
            )
        ]
        
        score = engine.score(entities, prompt_length=50)
        
        assert score.risk_level == RiskLevel.RED
        assert score.high_confidence_count == 1
    
    def test_very_long_prompt_amber(self, engine):
        """Test that very long prompts with entities are AMBER"""
        entities = [
            DetectedEntity(
                type=EntityType.PII,
                value="test@example.com",
                start_index=5000,
                end_index=5016,
                confidence=0.6,
                gliner_label="email"
            )
        ]
        
        score = engine.score(entities, prompt_length=15000)
        
        assert score.risk_level == RiskLevel.AMBER
    
    def test_empty_prompt_green(self, engine):
        """Test that empty prompt results in GREEN"""
        score = engine.score([], prompt_length=0)
        
        assert score.risk_level == RiskLevel.GREEN
    
    def test_custom_thresholds(self):
        """Test that custom thresholds work correctly"""
        engine = RiskScoringEngine(
            amber_min_entities=2,
            red_min_entities=5,
            high_confidence_threshold=0.8
        )
        
        # 1 entity should be GREEN with amber_min=2
        entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.6, "person")
        ]
        score = engine.score(entities, prompt_length=50)
        assert score.risk_level == RiskLevel.GREEN
        
        # 2 entities should be AMBER
        entities.append(
            DetectedEntity(EntityType.PII, "Jane", 10, 14, 0.6, "person")
        )
        score = engine.score(entities, prompt_length=50)
        assert score.risk_level == RiskLevel.AMBER
    
    def test_update_thresholds(self, engine):
        """Test updating thresholds dynamically"""
        engine.update_thresholds(
            amber_min_entities=3,
            red_min_entities=6,
            high_confidence_threshold=0.85
        )
        
        assert engine.amber_min_entities == 3
        assert engine.red_min_entities == 6
        assert engine.high_confidence_threshold == 0.85
    
    def test_mixed_entity_types(self, engine):
        """Test scoring with mixed entity types"""
        entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.65, "person"),
            DetectedEntity(EntityType.FINANCIAL, "1234-5678", 10, 19, 0.65, "account"),
            DetectedEntity(EntityType.CONTRACT, "Agreement", 25, 34, 0.6, "contract"),
        ]
        
        score = engine.score(entities, prompt_length=100)
        
        # Should be AMBER (3 entities, low-medium confidence)
        assert score.risk_level == RiskLevel.AMBER
        assert score.entity_count == 3
    
    def test_confidence_calculations(self, engine):
        """Test that confidence metrics are calculated correctly"""
        entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.6, "person"),
            DetectedEntity(EntityType.PII, "jane@example.com", 10, 26, 0.9, "email"),
            DetectedEntity(EntityType.PII, "555-1234", 30, 38, 0.5, "phone"),
        ]
        
        score = engine.score(entities, prompt_length=100)
        
        assert score.entity_count == 3
        assert score.high_confidence_count == 1  # Only email >= 0.7
        assert score.max_confidence == 0.9
    
    def test_reasoning_messages(self, engine):
        """Test that reasoning messages are provided"""
        # GREEN case
        score = engine.score([], prompt_length=100)
        assert len(score.reasoning) > 0
        assert "no sensitive data" in score.reasoning.lower()
        
        # AMBER case
        entities = [
            DetectedEntity(EntityType.PII, "John", 0, 4, 0.6, "person")
        ]
        score = engine.score(entities, prompt_length=100)
        assert len(score.reasoning) > 0
        
        # RED case
        entities = [
            DetectedEntity(EntityType.PII, "test@example.com", 0, 16, 0.95, "email")
        ]
        score = engine.score(entities, prompt_length=100)
        assert len(score.reasoning) > 0
