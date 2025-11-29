"""Classification endpoint for prompt analysis"""
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.classification import get_classification_service, DetectedEntity as ClassificationDetectedEntity
from app.risk_scoring import calculate_risk_level

router = APIRouter(prefix="/api/v1", tags=["classification"])


class ClassifyRequest(BaseModel):
    """Request model for classification"""
    text: str = Field(..., description="Text to classify for sensitive entities")
    threshold: float = Field(0.5, ge=0.0, le=1.0, description="Confidence threshold for entity detection")


class DetectedEntity(BaseModel):
    """Detected entity in the text"""
    type: str
    value: str
    start_index: int
    end_index: int
    confidence: float


class ClassifyResponse(BaseModel):
    """Response model for classification"""
    risk_level: str = Field(..., description="Risk level: green, amber, or red")
    detected_entities: List[DetectedEntity]
    confidence: float = Field(..., description="Overall confidence score")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


@router.post("/classify", response_model=ClassifyResponse)
async def classify_text(request: ClassifyRequest):
    """
    Classify text for sensitive entities using GLiNER model.
    Returns risk level and detected entities.
    
    Requirements: 2.1, 2.5, 2.6
    """
    try:
        # Get classification service
        service = get_classification_service()
        
        # Classify the text
        import time
        start_time = time.time()
        
        entities = service.classify(request.text, threshold=request.threshold)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert entities to response format
        detected_entities = [
            DetectedEntity(
                type=entity.type.value,
                value=entity.value,
                start_index=entity.start_index,
                end_index=entity.end_index,
                confidence=entity.confidence
            )
            for entity in entities
        ]
        
        # Calculate risk level
        risk_level = calculate_risk_level(entities)
        
        # Calculate overall confidence (average of entity confidences)
        confidence = sum(e.confidence for e in entities) / len(entities) if entities else 1.0
        
        return ClassifyResponse(
            risk_level=risk_level,
            detected_entities=detected_entities,
            confidence=confidence,
            processing_time_ms=processing_time_ms
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )
