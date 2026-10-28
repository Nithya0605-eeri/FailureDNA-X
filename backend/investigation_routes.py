from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .ai_investigator import run_ai_investigation


router = APIRouter(prefix="/api", tags=["AI Investigation"])


class GPUMetrics(BaseModel):
    gpu_id: str
    temperature_c: float = Field(ge=0, le=150)
    memory_usage_percent: float = Field(ge=0, le=100)
    gpu_utilization_percent: float = Field(ge=0, le=100)
    network_latency_ms: float = Field(ge=0)


class InvestigationRequest(BaseModel):
    gpu: GPUMetrics
    symptoms: dict[str, bool]
    max_tests: int = Field(default=3, ge=1, le=3)


@router.post("/investigate")
def investigate(request: InvestigationRequest):
    try:
        result = run_ai_investigation(
            gpu=request.gpu.model_dump(),
            symptoms=request.symptoms,
            max_tests=request.max_tests,
        )

        return {
            "success": True,
            "investigation": result,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="AI investigation failed. Check backend logs."
        )