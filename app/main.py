import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

from app.database import init_db
from app.routers.video import router as video_router
from app.models import HealthResponse

# Load environment variables
load_dotenv()

# 项目根目录（server/ 的上一级 = 2026_0508_digitalhuman/）
PROJECT_ROOT = Path(__file__).parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="DigitalArk - 数字方舟",
    description="数字人视频生成平台 - 基于火山引擎 Seedance 2.0",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (API routes take priority)
app.include_router(video_router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


# 前端静态文件挂载（指向 PROJECT_ROOT/app/）
frontend_dir = PROJECT_ROOT / "app"
if frontend_dir.exists() and (frontend_dir / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# SPA 兜底路由（所有未匹配的非API路径返回 index.html）
@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve index.html for any non-API path (SPA routing)."""
    if path.startswith("api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({"detail": "Not found"}, status_code=404)


# 根路径也返回 index.html
@app.get("/")
async def root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({"message": "DigitalArk API is running. Append /docs for Swagger UI."})
