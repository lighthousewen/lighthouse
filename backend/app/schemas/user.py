from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class OnboardingAnswer(BaseModel):
    question_id: int
    answer: str


class OnboardingRequest(BaseModel):
    user_id: str
    answers: list[OnboardingAnswer]


class OnboardingResult(BaseModel):
    user_id: str
    primary_type: str
    confidence: float
    state: str


class UserProfileOut(BaseModel):
    user_id: str
    primary_type: str
    state: str
    confidence: float
    assessment_done: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
