from fastapi import APIRouter
from pydantic import BaseModel
from app.core.phase_model import detect_phase, format_phase_context, get_phase_summary, UNKNOWN_PHASE, get_phase_by_id, PHASES

router = APIRouter(prefix="/api/v1/phase")


class PhaseAnalyzeRequest(BaseModel):
    signals: list[str] = []


class PhaseInfo(BaseModel):
    id: int
    name: str
    duration_text: str
    core_logic: str
    position_range: str
    sub_phase_count: int


class PhaseAnalyzeResult(BaseModel):
    phase: PhaseInfo
    context: str


@router.get("/summary")
async def phase_summary():
    return {"summary": get_phase_summary()}


@router.post("/analyze", response_model=PhaseAnalyzeResult)
async def phase_analyze(body: PhaseAnalyzeRequest):
    phase = detect_phase(body.signals)

    return PhaseAnalyzeResult(
        phase=PhaseInfo(
            id=phase.id,
            name=phase.name,
            duration_text=phase.duration_text,
            core_logic=phase.core_logic,
            position_range=phase.position_range,
            sub_phase_count=len(phase.sub_phases),
        ),
        context=format_phase_context(phase),
    )


@router.get("/phases")
async def list_phases():
    result = []
    for p in [UNKNOWN_PHASE] + list(PHASES):
        result.append({
            "id": p.id,
            "name": p.name,
            "duration": p.duration_text,
            "core_logic": p.core_logic,
            "position_range": p.position_range,
            "sub_phases": [
                {"id": sp.id, "name": sp.name, "signal": sp.signal}
                for sp in p.sub_phases
            ],
        })
    return {"phases": result}
