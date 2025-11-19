"""
Sanitization engine for removing sensitive data from prompts.
Provides multiple strategies: placeholder replacement, masking, and redaction.
"""
from typing import List, Literal, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.classification import DetectedEntity, EntityType


class SanitizationStrategy(str, Enum):
    """Strategy for sanitizing sensitive data"""
    REPLACE = "replace"  # Replace with typed placeholders
    MASK = "mask"        # Partially mask the value
    REDACT = "redact"    # Complete removal


@dataclass
class Replacement:
    """Represents a replacement made during sanitization"""
    original: str
    placeholder: str
    type: str
    start_index: int
    end_index: int


@dataclass
class SanitizationResult:
    """Result of sanitizing a prompt"""
    sanitized_prompt: str
    replacements: List[Replacement]
    is_fully_sanitized: bool


@dataclass
class DiffSpan:
    """Represents a span in the diff visualization"""
    text: str
    is_changed: bool
    entity_type: Optional[str] = None
    start_index: int = 0
    end_index: int = 0


@dataclass
class DiffResult:
    """Result of generating a diff between original and sanitized prompts"""
    original: str
    sanitized: str
    spans: List[DiffSpan]
    num_changes: int


class SanitizationEngine:
    """
    Engine for sanitizing prompts by replacing sensitive data with placeholders.
    Supports multiple sanitization strategies and preserves prompt structure.
    """
    
    # Mapping from entity types to placeholder names
    PLACEHOLDER_MAPPING = {
        EntityType.PII: {
            "person": "[PERSON]",
            "name": "[NAME]",
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "phone number": "[PHONE]",
            "address": "[ADDRESS]",
            "location": "[LOCATION]",
            "date of birth": "[DATE_OF_BIRTH]",
            "ssn": "[SSN]",
            "social security number": "[SSN]",
            "passport": "[PASSPORT]",
            "driver license": "[DRIVER_LICENSE]",
            "ip address": "[IP_ADDRESS]",
            "medical": "[MEDICAL_INFO]",
            "health": "[MEDICAL_INFO]",
        },
        EntityType.FINANCIAL: {
            "credit card": "[CREDIT_CARD]",
            "credit card number": "[CREDIT_CARD]",
            "account number": "[ACCOUNT_NUMBER]",
            "bank account": "[ACCOUNT_NUMBER]",
            "iban": "[IBAN]",
            "routing number": "[ROUTING_NUMBER]",
            "amount": "[AMOUNT]",
            "money": "[AMOUNT]",
            "transaction": "[TRANSACTION]",
        },
        EntityType.CONTRACT: {
            "contract": "[CONTRACT]",
            "agreement": "[AGREEMENT]",
            "legal": "[LEGAL_DOCUMENT]",
        },
        EntityType.IP: {
            "patent": "[PATENT]",
            "trademark": "[TRADEMARK]",
            "copyright": "[COPYRIGHT]",
            "trade secret": "[TRADE_SECRET]",
        },
        EntityType.CUSTOM: {
            "custom": "[SENSITIVE_DATA]",
        }
    }
    
    def __init__(self, default_strategy: SanitizationStrategy = SanitizationStrategy.REPLACE):
        """
        Initialize the sanitization engine.
        
        Args:
            default_strategy: Default strategy to use for sanitization
        """
        self.default_strategy = default_strategy
    
    def sanitize(
        self,
        prompt: str,
        entities: List[DetectedEntity],
        strategy: Optional[SanitizationStrategy] = None
    ) -> SanitizationResult:
        """
        Sanitize a prompt by replacing detected entities according to the strategy.
        
        Args:
            prompt: The original prompt text
            entities: List of detected sensitive entities
            strategy: Sanitization strategy to use (defaults to instance default)
        
        Returns:
            SanitizationResult with sanitized prompt and replacement details
        """
        if not entities:
            return SanitizationResult(
                sanitized_prompt=prompt,
                replacements=[],
                is_fully_sanitized=True
            )
        
        strategy = strategy or self.default_strategy
        
        # Sort entities by start index in reverse order to maintain correct indices
        sorted_entities = sorted(entities, key=lambda e: e.start_index, reverse=True)
        
        sanitized_text = prompt
        replacements = []
        
        for entity in sorted_entities:
            # Get the replacement text based on strategy
            if strategy == SanitizationStrategy.REPLACE:
                replacement_text = self._get_placeholder(entity)
            elif strategy == SanitizationStrategy.MASK:
                replacement_text = self._mask_value(entity.value)
            elif strategy == SanitizationStrategy.REDACT:
                replacement_text = ""
            else:
                replacement_text = self._get_placeholder(entity)
            
            # Replace the entity in the text
            sanitized_text = (
                sanitized_text[:entity.start_index] +
                replacement_text +
                sanitized_text[entity.end_index:]
            )
            
            # Record the replacement
            replacement = Replacement(
                original=entity.value,
                placeholder=replacement_text,
                type=entity.gliner_label,
                start_index=entity.start_index,
                end_index=entity.end_index
            )
            replacements.append(replacement)
        
        # Reverse replacements to maintain original order
        replacements.reverse()
        
        return SanitizationResult(
            sanitized_prompt=sanitized_text,
            replacements=replacements,
            is_fully_sanitized=True
        )
    
    def _get_placeholder(self, entity: DetectedEntity) -> str:
        """
        Get the appropriate placeholder for an entity.
        
        Args:
            entity: The detected entity
        
        Returns:
            Placeholder string for the entity
        """
        # Normalize the label
        normalized_label = entity.gliner_label.lower().strip()
        
        # Look up placeholder in the mapping
        if entity.type in self.PLACEHOLDER_MAPPING:
            type_mapping = self.PLACEHOLDER_MAPPING[entity.type]
            
            # Try exact match
            if normalized_label in type_mapping:
                return type_mapping[normalized_label]
            
            # Try partial match
            for key, placeholder in type_mapping.items():
                if key in normalized_label or normalized_label in key:
                    return placeholder
        
        # Default placeholder based on entity type
        return f"[{entity.type.value.upper()}]"
    
    def _mask_value(self, value: str) -> str:
        """
        Partially mask a sensitive value.
        
        Args:
            value: The value to mask
        
        Returns:
            Masked version of the value
        """
        if not value:
            return "***"
        
        length = len(value)
        
        # For very short values, mask completely
        if length <= 3:
            return "***"
        
        # For email addresses, mask the local part
        if "@" in value:
            local, domain = value.split("@", 1)
            if len(local) <= 2:
                masked_local = "***"
            else:
                masked_local = local[0] + "***" + local[-1]
            return f"{masked_local}@{domain}"
        
        # For phone numbers (contains digits and dashes/spaces)
        if any(c.isdigit() for c in value):
            # Show last 4 characters
            if length > 4:
                return "***-**-" + value[-4:]
            else:
                return "***" + value[-1:]
        
        # For other values, show first and last character
        if length <= 4:
            return value[0] + "***"
        else:
            return value[0] + "***" + value[-1]
    
    def generate_diff(self, original: str, sanitized: str, replacements: List[Replacement]) -> DiffResult:
        """
        Generate a diff visualization between original and sanitized prompts.
        
        Args:
            original: The original prompt text
            sanitized: The sanitized prompt text
            replacements: List of replacements made during sanitization
        
        Returns:
            DiffResult with spans highlighting changes
        """
        if not replacements:
            # No changes, return single span
            return DiffResult(
                original=original,
                sanitized=sanitized,
                spans=[DiffSpan(text=original, is_changed=False)],
                num_changes=0
            )
        
        # Sort replacements by start index
        sorted_replacements = sorted(replacements, key=lambda r: r.start_index)
        
        spans = []
        current_pos = 0
        
        for replacement in sorted_replacements:
            # Add unchanged text before this replacement
            if current_pos < replacement.start_index:
                unchanged_text = original[current_pos:replacement.start_index]
                if unchanged_text:
                    spans.append(DiffSpan(
                        text=unchanged_text,
                        is_changed=False,
                        start_index=current_pos,
                        end_index=replacement.start_index
                    ))
            
            # Add the changed span (original value)
            spans.append(DiffSpan(
                text=replacement.original,
                is_changed=True,
                entity_type=replacement.type,
                start_index=replacement.start_index,
                end_index=replacement.end_index
            ))
            
            current_pos = replacement.end_index
        
        # Add any remaining unchanged text
        if current_pos < len(original):
            remaining_text = original[current_pos:]
            if remaining_text:
                spans.append(DiffSpan(
                    text=remaining_text,
                    is_changed=False,
                    start_index=current_pos,
                    end_index=len(original)
                ))
        
        return DiffResult(
            original=original,
            sanitized=sanitized,
            spans=spans,
            num_changes=len(replacements)
        )
    
    def format_diff_text(self, diff: DiffResult) -> str:
        """
        Format a diff result as human-readable text with annotations.
        
        Args:
            diff: The diff result to format
        
        Returns:
            Formatted text representation of the diff
        """
        lines = []
        lines.append("=== ORIGINAL ===")
        
        for span in diff.spans:
            if span.is_changed:
                lines.append(f"[DETECTED: {span.entity_type}] {span.text}")
            else:
                lines.append(span.text)
        
        lines.append("\n=== SANITIZED ===")
        lines.append(diff.sanitized)
        
        lines.append(f"\n=== SUMMARY ===")
        lines.append(f"Total changes: {diff.num_changes}")
        
        return "\n".join(lines)
