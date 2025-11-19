#!/usr/bin/env python3
"""
Test script to diagnose issues with knowledgator/gliner-pii-edge-v1.0 model
"""
from gliner import GLiNER

def test_model(model_name):
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}\n")
    
    try:
        print("Loading model...")
        model = GLiNER.from_pretrained(model_name)
        print("✓ Model loaded successfully\n")
        
        # Test text
        text = "My name is John Smith and my email is john@example.com. Call me at 555-123-4567."
        
        # Try different label sets
        label_sets = [
            # Original labels from current code
            ["person", "email", "phone number", "address", "credit card number",
             "social security number", "date of birth", "passport", "driver license",
             "bank account", "ip address", "medical", "organization", "location"],
            
            # Simplified labels
            ["person", "email", "phone", "address"],
            
            # Generic PII labels
            ["name", "email", "phone number", "address", "ssn", "credit card"],
            
            # Empty (let model decide)
            []
        ]
        
        for i, labels in enumerate(label_sets, 1):
            print(f"\nTest {i}: Labels = {labels if labels else 'AUTO-DETECT'}")
            print("-" * 60)
            
            try:
                if labels:
                    entities = model.predict_entities(text, labels, threshold=0.3)
                else:
                    # Some models support auto-detection
                    entities = model.predict_entities(text, threshold=0.3)
                
                print(f"Found {len(entities)} entities:")
                for entity in entities:
                    print(f"  - {entity['label']}: '{entity['text']}' (score: {entity['score']:.3f})")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        print(f"\n{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print(f"\n{'='*60}\n")
        return False


if __name__ == "__main__":
    # Test both models
    models = [
        #"urchade/gliner_small-v2.1",  # Current working model
        "knowledgator/gliner-pii-edge-v1.0"  # New model to test
    ]
    
    for model_name in models:
        test_model(model_name)
