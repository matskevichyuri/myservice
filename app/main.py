import os
import subprocess
import tempfile
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


@app.post("/api/3d/generate")
async def generate_3d(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Maximum image size is 10 MB")
    job_id = str(uuid.uuid4())
    work = Path(tempfile.gettempdir()) / f"myservice-{job_id}"
    work.mkdir(parents=True, exist_ok=True)
    glb_path, fbx_path = work / "model.glb", work / "model.fbx"
    input_path = work / Path(file.filename or "input.png").name
    input_path.write_bytes(data)
    result = subprocess.run(["python", "/opt/TripoSR/run.py", str(input_path), "--output-dir", str(work), "--model-save-format", "glb", "--bake-texture"], capture_output=True, text=True, timeout=300)
    candidates = list(work.rglob("*.glb"))
    if result.returncode != 0 or not candidates:
        raise HTTPException(status_code=500, detail=f"TripoSR generation failed: {result.stderr[-500:]}")
    candidates[0].replace(glb_path)
    script = BASE_DIR / "export_fbx.py"
    result = subprocess.run(["blender", "--background", "--python", str(script), "--", str(glb_path), str(fbx_path)], capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not fbx_path.exists():
        raise HTTPException(status_code=500, detail="Blender FBX conversion failed")
    return {"id": job_id, "format": "fbx", "download": f"/api/3d/{job_id}/download", "size": fbx_path.stat().st_size}


@app.get("/api/3d/{job_id}/download")
def download_3d(job_id: str):
    path = Path(tempfile.gettempdir()) / f"myservice-{job_id}" / "model.fbx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Model not found or expired")
    return FileResponse(path, media_type="application/octet-stream", filename=f"{job_id}.fbx")
