import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_NAME = "myservice"
BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Trellix Myservice API", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ScanRequest(BaseModel):
    target: str = Field(min_length=1, max_length=4096)
    target_type: str = Field(default="text", pattern="^(text|url|hash)$")


def trellix_configured() -> bool:
    return bool(os.getenv("TRELLIX_API_URL") and os.getenv("TRELLIX_API_TOKEN"))


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"service": APP_NAME, "status": "ok", "trellix_configured": trellix_configured()}


@app.get("/api/status")
def status():
    return {
        "service": APP_NAME,
        "provider": "Trellix",
        "mode": "connected" if trellix_configured() else "demo",
        "gpu": os.getenv("GPU_NAME", "NVIDIA GeForce RTX 5070 Ti"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/scan")
def scan(request: ScanRequest):
    # Integration point for the selected Trellix product/API.
    return {
        "id": str(uuid.uuid4()),
        "target_type": request.target_type,
        "verdict": "unknown" if not trellix_configured() else "pending",
        "message": "Configure TRELLIX_API_URL and TRELLIX_API_TOKEN to enable live checks."
        if not trellix_configured() else "Request accepted for Trellix analysis.",
    }


@app.post("/api/scan/file")
async def scan_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Maximum file size is 25 MB")
    return {
        "id": str(uuid.uuid4()),
        "filename": file.filename,
        "size": len(content),
        "verdict": "unknown" if not trellix_configured() else "pending",
        "message": "Demo mode: file was received but not sent to Trellix.",
    }
