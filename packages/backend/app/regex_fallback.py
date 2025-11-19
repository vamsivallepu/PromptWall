"""
Regex-based fallback patterns for entity detection.
Used when GLiNER model is unavailable or to augment GLiNER results.
"""
import re
from typing import List, Pattern
from dataclasses import dataclass

from app.classification import DetectedEntity, EntityType


@dataclass
class RegexPattern:
    """Represents a regex pattern for entity detection"""
    name: str
    pattern: Pattern
    entity_type: EntityType
    confidence: float = 0.8  # Default confidence for regex matches


class RegexFallbackClassifier:
    """
    Fallback classifier using regex patterns for structured data detection.
    Complements GLiNER by catching patterns it might miss.
    """
    
    def __init__(self):
        """Initialize with predefined regex patterns"""
        self.patterns: List[RegexPattern] = self._initialize_patterns()
    
    def _initialize_patterns(self) -> List[RegexPattern]:
        """
        Initialize common regex patterns for PII and financial data.
        
        Returns:
            List of RegexPattern objects
        """
        patterns = []
        
        # Email pattern
        patterns.append(RegexPattern(
            name="email",
            pattern=re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            entity_type=EntityType.PII,
            confidence=0.95
        ))
        
        # Phone number patterns (various formats)
        # US format: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
        patterns.append(RegexPattern(
            name="phone",
            pattern=re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
            ),
            entity_type=EntityType.PII,
            confidence=0.85
        ))
        
        # International phone format: +XX XXX XXX XXXX
        patterns.append(RegexPattern(
            name="phone_international",
            pattern=re.compile(
                r'\+[0-9]{1,3}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,9}'
            ),
            entity_type=EntityType.PII,
            confidence=0.80
        ))
        
        # Credit card patterns (Visa, MasterCard, Amex, Discover)
        patterns.append(RegexPattern(
            name="credit_card",
            pattern=re.compile(
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|'  # Visa
                r'5[1-5][0-9]{14}|'  # MasterCard
                r'3[47][0-9]{13}|'  # American Express
                r'6(?:011|5[0-9]{2})[0-9]{12})\b'  # Discover
            ),
            entity_type=EntityType.FINANCIAL,
            confidence=0.90
        ))
        
        # Credit card with spaces or dashes
        patterns.append(RegexPattern(
            name="credit_card_formatted",
            pattern=re.compile(
                r'\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))'
                r'[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b'
            ),
            entity_type=EntityType.FINANCIAL,
            confidence=0.90
        ))
        
        # SSN patterns: XXX-XX-XXXX or XXXXXXXXX
        patterns.append(RegexPattern(
            name="ssn",
            pattern=re.compile(
                r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b'
            ),
            entity_type=EntityType.PII,
            confidence=0.85
        ))
        
        # IP Address (IPv4)
        patterns.append(RegexPattern(
            name="ip_address",
            pattern=re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            entity_type=EntityType.PII,
            confidence=0.75
        ))
        
        # Bank account number (generic pattern, 8-17 digits)
        patterns.append(RegexPattern(
            name="account_number",
            pattern=re.compile(
                r'\b(?:account|acct|acc)[\s#:]*([0-9]{8,17})\b',
                re.IGNORECASE
            ),
            entity_type=EntityType.FINANCIAL,
            confidence=0.70
        ))
        
        # IBAN (International Bank Account Number)
        patterns.append(RegexPattern(
            name="iban",
            pattern=re.compile(
                r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b'
            ),
            entity_type=EntityType.FINANCIAL,
            confidence=0.85
        ))
        
        # Passport number (generic pattern)
        patterns.append(RegexPattern(
            name="passport",
            pattern=re.compile(
                r'\b(?:passport|pass)[\s#:]*([A-Z0-9]{6,9})\b',
                re.IGNORECASE
            ),
            entity_type=EntityType.PII,
            confidence=0.70
        ))
        
        return patterns
    
    def classify(self, text: str) -> List[DetectedEntity]:
        """
        Classify text using regex patterns to detect structured data.
        
        Args:
            text: The text to analyze
        
        Returns:
            List of detected entities
        """
        if not text or not text.strip():
            return []
        
        detected_entities = []
        
        for regex_pattern in self.patterns:
            matches = regex_pattern.pattern.finditer(text)
            
            for match in matches:
                entity = DetectedEntity(
                    type=regex_pattern.entity_type,
                    value=match.group(0),
                    start_index=match.start(),
                    end_index=match.end(),
                    confidence=regex_pattern.confidence,
                    gliner_label=regex_pattern.name  # Use pattern name as label
                )
                detected_entities.append(entity)
        
        return detected_entities
    
    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        entity_type: EntityType,
        confidence: float = 0.8
    ) -> None:
        """
        Add a custom regex pattern for organization-specific sensitive data.
        
        Args:
            name: Name/identifier for the pattern
            pattern: Regex pattern string
            entity_type: Type of entity this pattern detects
            confidence: Confidence score for matches (0.0-1.0)
        """
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            regex_pattern = RegexPattern(
                name=name,
                pattern=compiled_pattern,
                entity_type=entity_type,
                confidence=confidence
            )
            self.patterns.append(regex_pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")


def merge_entities(
    gliner_entities: List[DetectedEntity],
    regex_entities: List[DetectedEntity],
    overlap_threshold: float = 0.5
) -> List[DetectedEntity]:
    """
    Merge GLiNER and regex detection results, deduplicating overlapping detections.
    
    Args:
        gliner_entities: Entities detected by GLiNER
        regex_entities: Entities detected by regex patterns
        overlap_threshold: Minimum overlap ratio to consider entities as duplicates
    
    Returns:
        Merged list of unique entities
    """
    if not gliner_entities:
        return regex_entities
    if not regex_entities:
        return gliner_entities
    
    merged = gliner_entities.copy()
    
    for regex_entity in regex_entities:
        is_duplicate = False
        
        for gliner_entity in gliner_entities:
            if _entities_overlap(regex_entity, gliner_entity, overlap_threshold):
                is_duplicate = True
                break
        
        if not is_duplicate:
            merged.append(regex_entity)
    
    # Sort by start index for consistent ordering
    merged.sort(key=lambda e: e.start_index)
    
    return merged


def _entities_overlap(entity1: DetectedEntity, entity2: DetectedEntity, threshold: float) -> bool:
    """
    Check if two entities overlap significantly.
    
    Args:
        entity1: First entity
        entity2: Second entity
        threshold: Minimum overlap ratio (0.0-1.0)
    
    Returns:
        True if entities overlap above threshold
    """
    # Calculate overlap
    start = max(entity1.start_index, entity2.start_index)
    end = min(entity1.end_index, entity2.end_index)
    
    if start >= end:
        return False  # No overlap
    
    overlap_length = end - start
    
    # Calculate overlap ratio relative to shorter entity
    entity1_length = entity1.end_index - entity1.start_index
    entity2_length = entity2.end_index - entity2.start_index
    min_length = min(entity1_length, entity2_length)
    
    if min_length == 0:
        return False
    
    overlap_ratio = overlap_length / min_length
    
    return overlap_ratio >= threshold


# Global instance
_regex_classifier: RegexFallbackClassifier = None


def get_regex_classifier() -> RegexFallbackClassifier:
    """
    Get or create the global regex fallback classifier instance.
    
    Returns:
        RegexFallbackClassifier instance
    """
    global _regex_classifier
    
    if _regex_classifier is None:
        _regex_classifier = RegexFallbackClassifier()
    
    return _regex_classifier
