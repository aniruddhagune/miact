import sys
import asyncio
import os

# ---- Windows Asyncio Fix (MUST BE TOP) ----
if sys.platform == 'win32':
    try:
        # Check if already set to avoid re-setting
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        pass

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import traceback

from backend.database.schema_manager import initialize_db
from backend.utils.logger import logger
from backend.routes import query, search, debug, config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    logger.info("SYSTEM", "MIACT Backend starting up...")
    initialize_db()
    yield
    # Shutdown: Clean up resources if needed
    logger.info("SYSTEM", "MIACT Backend shutting down...")

app = FastAPI(lifespan=lifespan)

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_exceptions_middleware(request: Request, call_next):
    # Skip logging for static assets
    if request.url.path.startswith("/assets") or request.url.path.endswith((".js", ".css", ".png", ".svg", ".ico")):
        return await call_next(request)
        
    logger.info("SYSTEM", f"Incoming Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.debug("SYSTEM", f"Response Status: {response.status_code} for {request.url}")
        return response
    except Exception as e:
        logger.error("SYSTEM", f"Unhandled Exception during {request.method} {request.url}: {e}")
        logger.error("SYSTEM", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "detail": str(e)}
        )

# Include Routers (API prefix suggested for packaged version)
app.include_router(query.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(debug.router, prefix="/api")
app.include_router(config.router, prefix="/api")

# Serve Frontend Static Files
# Priority: Check for frontend/dist (dev repo) or ./frontend (packaged)
frontend_path = "frontend/dist"
if not os.path.exists(frontend_path):
    # Check relative to script (for PyInstaller)
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    frontend_path = os.path.join(base_path, "frontend")

if os.path.exists(frontend_path):
    logger.info("SYSTEM", f"Serving frontend from: {frontend_path}")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve index.html for any unknown routes (SPA support)
        # But only if it doesn't look like an API call
        if not full_path.startswith("api/"):
            return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    logger.warning("SYSTEM", "Frontend build directory not found. API-only mode.")
    @app.get("/")
    def root():
        return {"message": "MIACT API is running (No Frontend)", "status": "online"}

@app.get("/favicon.ico")
def favicon():
    return {}
