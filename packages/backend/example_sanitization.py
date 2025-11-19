"""
Example demonstrating the sanitization engine with classification.
This shows the complete flow: classify -> sanitize -> generate diff.
"""
from app.classification import get_classification_service
from app.sanitization import SanitizationEngine, SanitizationStrategy


def main():
    # Initialize services
    print("Initializing classification service...")
    classifier = get_classification_service()
    sanitizer = SanitizationEngine()
    
    # Example prompt with sensitive data
    prompt = """
    Hi, I'm John Smith and my email is john.smith@company.com.
    You can reach me at 555-123-4567 or use my credit card 4532-1234-5678-9010.
    My SSN is 123-45-6789 for verification.
    """
    
    print("\n" + "="*80)
    print("ORIGINAL PROMPT:")
    print("="*80)
    print(prompt)
    
    # Step 1: Classify the prompt
    print("\n" + "="*80)
    print("STEP 1: CLASSIFICATION")
    print("="*80)
    entities = classifier.classify(prompt.strip(), threshold=0.5)
    print(f"Found {len(entities)} sensitive entities:")
    for entity in entities:
        print(f"  - {entity.gliner_label}: '{entity.value}' "
              f"(confidence: {entity.confidence:.2f}, type: {entity.type.value})")
    
    # Step 2: Sanitize with REPLACE strategy (default)
    print("\n" + "="*80)
    print("STEP 2: SANITIZATION (REPLACE STRATEGY)")
    print("="*80)
    result = sanitizer.sanitize(prompt.strip(), entities)
    print("Sanitized prompt:")
    print(result.sanitized_prompt)
    print(f"\nReplacements made: {len(result.replacements)}")
    for replacement in result.replacements:
        print(f"  - '{replacement.original}' -> '{replacement.placeholder}'")
    
    # Step 3: Generate diff
    print("\n" + "="*80)
    print("STEP 3: DIFF VISUALIZATION")
    print("="*80)
    diff = sanitizer.generate_diff(prompt.strip(), result.sanitized_prompt, result.replacements)
    print(sanitizer.format_diff_text(diff))
    
    # Step 4: Try MASK strategy
    print("\n" + "="*80)
    print("STEP 4: SANITIZATION (MASK STRATEGY)")
    print("="*80)
    mask_result = sanitizer.sanitize(prompt.strip(), entities, strategy=SanitizationStrategy.MASK)
    print("Masked prompt:")
    print(mask_result.sanitized_prompt)
    
    # Step 5: Try REDACT strategy
    print("\n" + "="*80)
    print("STEP 5: SANITIZATION (REDACT STRATEGY)")
    print("="*80)
    redact_result = sanitizer.sanitize(prompt.strip(), entities, strategy=SanitizationStrategy.REDACT)
    print("Redacted prompt:")
    print(redact_result.sanitized_prompt)
    
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
