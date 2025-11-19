"""
Risk scoring algorithm for classifying prompts by sensitivity level.
"""
from typing import List
from enum import Enum
from dataclasses import dataclass

from app.classification import DetectedEntity, EntityType


class RiskLevel(str, Enum):
    """Risk level classification for prompts"""
    GREEN = "green"   # No sensitive data detected
    AMBER = "amber"   # Low to medium sensitivity
    RED = "red"       # High sensitivity


@dataclass
class RiskScore:
    """Result of risk scoring analysis"""
    risk_level: RiskLevel
    entity_count: int
    high_confidence_count: int
    max_confidence: float
    reasoning: str


class RiskScoringEngine:
    """
    Engine for scoring prompts based on detected entities and assigning risk levels.
    
    Risk Level Rules:
    - GREEN: No sensitive data detected
    - AMBER: 1-3 sensitive entities OR low-confidence detections (score < 0.7)
    - RED: 4+ sensitive entities OR high-confidence PII/financial data (score >= 0.7)
    """
    
    # Configuration thresholds
    DEFAULT_AMBER_MIN_ENTITIES = 1
    DEFAULT_RED_MIN_ENTITIES = 4
    DEFAULT_HIGH_CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(
        self,
        amber_min_entities: int = DEFAULT_AMBER_MIN_ENTITIES,
        red_min_entities: int = DEFAULT_RED_MIN_ENTITIES,
        high_confidence_threshold: float = DEFAULT_HIGH_CONFIDENCE_THRESHOLD
    ):
        """
        Initialize the risk scoring engine with configurable thresholds.
        
        Args:
            amber_min_entities: Minimum entities to trigger amber level
            red_min_entities: Minimum entities to trigger red level
            high_confidence_threshold: Confidence score threshold for high-risk classification
        """
        self.amber_min_entities = amber_min_entities
        self.red_min_entities = red_min_entities
        self.high_confidence_threshold = high_confidence_threshold
    
    def score(self, entities: List[DetectedEntity], prompt_length: int = 0) -> RiskScore:
        """
        Score a prompt based on detected entities and assign a risk level.
        
        Args:
            entities: List of detected entities from classification
            prompt_length: Length of the original prompt (for edge case handling)
        
        Returns:
            RiskScore with level, counts, and reasoning
        """
        # Handle edge case: empty prompt
        if prompt_length == 0 or not entities:
            return RiskScore(
                risk_level=RiskLevel.GREEN,
                entity_count=0,
                high_confidence_count=0,
                max_confidence=0.0,
                reasoning="No sensitive data detected"
            )
        
        # Handle edge case: very long prompts (>10000 chars) - be more conservative
        is_very_long = prompt_length > 10000
        
        # Calculate metrics
        entity_count = len(entities)
        high_confidence_entities = [e for e in entities if e.confidence >= self.high_confidence_threshold]
        high_confidence_count = len(high_confidence_entities)
        max_confidence = max((e.confidence for e in entities), default=0.0)
        
        # Count high-risk entity types (PII and Financial)
        high_risk_entities = [
            e for e in entities 
            if e.type in (EntityType.PII, EntityType.FINANCIAL)
        ]
        high_risk_count = len(high_risk_entities)
        
        # Determine risk level based on rules
        risk_level, reasoning = self._determine_risk_level(
            entity_count=entity_count,
            high_confidence_count=high_confidence_count,
            high_risk_count=high_risk_count,
            max_confidence=max_confidence,
            is_very_long=is_very_long
        )
        
        return RiskScore(
            risk_level=risk_level,
            entity_count=entity_count,
            high_confidence_count=high_confidence_count,
            max_confidence=max_confidence,
            reasoning=reasoning
        )
    
    def _determine_risk_level(
        self,
        entity_count: int,
        high_confidence_count: int,
        high_risk_count: int,
        max_confidence: float,
        is_very_long: bool
    ) -> tuple[RiskLevel, str]:
        """
        Determine the risk level based on entity metrics.
        
        Returns:
            Tuple of (RiskLevel, reasoning string)
        """
        # Rule 1: No entities = GREEN
        if entity_count == 0:
            return RiskLevel.GREEN, "No sensitive data detected"
        
        # Rule 2: High-confidence PII/Financial data = RED
        if high_confidence_count > 0 and high_risk_count > 0 and max_confidence >= self.high_confidence_threshold:
            return (
                RiskLevel.RED,
                f"High-confidence sensitive data detected ({high_confidence_count} entities with confidence >= {self.high_confidence_threshold})"
            )
        
        # Rule 3: Many entities (4+) = RED
        if entity_count >= self.red_min_entities:
            return (
                RiskLevel.RED,
                f"Multiple sensitive entities detected ({entity_count} entities)"
            )
        
        # Rule 4: Very long prompts with any entities = AMBER (conservative)
        if is_very_long and entity_count > 0:
            return (
                RiskLevel.AMBER,
                f"Sensitive data detected in very long prompt ({entity_count} entities)"
            )
        
        # Rule 5: 1-3 entities = AMBER
        if entity_count >= self.amber_min_entities:
            if max_confidence < self.high_confidence_threshold:
                return (
                    RiskLevel.AMBER,
                    f"Low-confidence sensitive data detected ({entity_count} entities, max confidence {max_confidence:.2f})"
                )
            else:
                return (
                    RiskLevel.AMBER,
                    f"Sensitive data detected ({entity_count} entities)"
                )
        
        # Default: GREEN (shouldn't reach here if entity_count > 0, but safety fallback)
        return RiskLevel.GREEN, "No significant sensitive data detected"
    
    def update_thresholds(
        self,
        amber_min_entities: int = None,
        red_min_entities: int = None,
        high_confidence_threshold: float = None
    ) -> None:
        """
        Update the risk scoring thresholds.
        
        Args:
            amber_min_entities: New minimum entities for amber level
            red_min_entities: New minimum entities for red level
            high_confidence_threshold: New confidence threshold
        """
        if amber_min_entities is not None:
            self.amber_min_entities = amber_min_entities
        if red_min_entities is not None:
            self.red_min_entities = red_min_entities
        if high_confidence_threshold is not None:
            self.high_confidence_threshold = high_confidence_threshold


# Global instance
_risk_scoring_engine: RiskScoringEngine = None


def get_risk_scoring_engine() -> RiskScoringEngine:
    """
    Get or create the global risk scoring engine instance.
    
    Returns:
        RiskScoringEngine instance
    """
    global _risk_scoring_engine
    
    if _risk_scoring_engine is None:
        _risk_scoring_engine = RiskScoringEngine()
    
    return _risk_scoring_engine
