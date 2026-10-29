"""FastAPI Application Main Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes.simulation import router as sim_router
from api.routes.agents import router as agents_router
from api.routes.metrics import router as metrics_router
from api.routes.copilot import router as copilot_router

app = FastAPI(
    title="Resilient Multi-Agent Energy Management System (Resilient-MAS)",
    description="Cyber-Physical Energy Management, Trust Modeling, and RAG Copilot on IEEE 33-Bus with Ember & OPSD Data",
    version="1.0.0"
)

# Enable CORS for local dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(sim_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(copilot_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "Resilient-MAS IEEE 33-Bus"}

# Serve Frontend Dashboard static files if dashboard directory exists
dashboard_dir = Path("dashboard")
if dashboard_dir.exists():
    app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")

