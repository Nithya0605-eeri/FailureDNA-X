"""
HTTP routes for the simulated (hidden-fault) investigation.
Your partner adds two lines to backend/main.py to switch them on:

    from backend.sim_routes1 import router as sim_router
    app.include_router(sim_router)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import sim_service1 as service

router = APIRouter(prefix="/api/sim", tags=["Simulated investigation"])


class CreateRequest(BaseModel):
    mode: str = "nemotron"           # nemotron | infogain | fixed
    seed: Optional[int] = None       # leave empty for a random hidden fault
    fault: Optional[str] = None      # rehearsal only: force a fault
    severity: Optional[str] = None   # rehearsal only: mild | severe


@router.get("/info")
def sim_info():
    return service.info()


@router.post("/investigations")
def create_investigation(req: CreateRequest):
    try:
        return service.create(req.mode, req.seed, req.fault, req.severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _call(fn, inv_id: str):
    try:
        return fn(inv_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Investigation not found (the server may have restarted).")


@router.post("/investigations/{inv_id}/step")
def step_investigation(inv_id: str):
    return _call(service.step, inv_id)


@router.post("/investigations/{inv_id}/run")
def run_investigation(inv_id: str):
    return _call(service.run, inv_id)


@router.get("/investigations/{inv_id}")
def get_investigation(inv_id: str):
    return _call(service.state, inv_id)