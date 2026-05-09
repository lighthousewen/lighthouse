from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models import UserProfile, AssessmentAnswer
from app.schemas.user import OnboardingRequest, OnboardingResult, UserProfileOut
from typing import Optional


ASSESSMENT_QUESTIONS = [
    {
        "id": 1,
        "question": "学新东西时，更接近哪种状态？",
        "options": {
            "A": "必须先理解底层，自己推一遍才觉得真会了",
            "B": "边用边学，不需要一开始就全懂",
            "C": "能用就行，如果有人帮弄好就不学了",
        },
    },
    {
        "id": 2,
        "question": "自己花了很多时间研究出一个结论，AI说'其实不用这么复杂，结论完全一样'——第一反应？",
        "options": {
            "A": "不后悔，过程是必要的",
            "B": "早知道问AI了",
            "C": "有点亏，但也不算白费",
        },
    },
    {
        "id": 3,
        "question": "AI说'这个框架很好，我可以直接帮你运行，你不需要自己操作了'——本能的第一反应？",
        "options": {
            "A": "不行，我想自己跑几遍先",
            "B": "太好了",
            "C": "先让它跑跑看，结果差不多就懒得自己跑了",
        },
    },
]

router = APIRouter(prefix="/api/v1")


@router.get("/assessment/questions")
async def get_assessment_questions():
    return {"questions": ASSESSMENT_QUESTIONS}


@router.post("/onboarding/assess", response_model=OnboardingResult)
async def onboarding_assess(body: OnboardingRequest, db: AsyncSession = Depends(get_db)):
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == body.user_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=body.user_id, state="UNKNOWN_RAW")
        db.add(profile)
        await db.flush()

    await db.execute(
        delete(AssessmentAnswer).where(AssessmentAnswer.user_id == body.user_id)
    )

    q1_answer = None
    q2_answer = None
    q3_answer = None

    for a in body.answers:
        answer = AssessmentAnswer(
            user_id=body.user_id,
            question_id=a.question_id,
            answer=a.answer,
        )
        db.add(answer)
        if a.question_id == 1:
            q1_answer = a.answer
        elif a.question_id == 2:
            q2_answer = a.answer
        elif a.question_id == 3:
            q3_answer = a.answer

    if q3_answer == "A":
        primary_type = "builder"
        confidence = 0.95
        state = "BUILDER"
    elif q3_answer == "B":
        primary_type = "user"
        confidence = 0.95
        state = "USER"
    else:
        if q1_answer == "A" and q2_answer == "A":
            primary_type = "builder"
            confidence = 0.70
            state = "BUILDER"
        else:
            primary_type = "user"
            confidence = 0.60
            state = "USER"

    profile.primary_type = primary_type
    profile.state = state
    profile.confidence = confidence
    profile.assessment_done = True

    return OnboardingResult(
        user_id=body.user_id,
        primary_type=primary_type,
        confidence=confidence,
        state=state,
    )


@router.get("/user/{user_id}", response_model=UserProfileOut)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=user_id, state="UNKNOWN_RAW")
        db.add(profile)
        await db.flush()
        return profile

    return profile


@router.put("/user/{user_id}/state")
async def update_user_state(user_id: str, state: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    valid_states = {"UNKNOWN_RAW", "UNKNOWN_ASSESSED", "BUILDER", "USER", "HYBRID"}
    if state not in valid_states:
        raise HTTPException(status_code=400, detail=f"Invalid state. Must be one of: {valid_states}")

    profile.state = state
    return {"user_id": user_id, "state": state}
