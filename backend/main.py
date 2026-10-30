from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.sim_routes1 import router as sim_router

from backend.investigation_routes import router as investigation_router

app = FastAPI(title="FailureDNA X API")

# Lets the React app (localhost:5173) call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigation_router)
app.include_router(sim_router)


@app.get("/health")
def health():
    return {"status": "ok"}