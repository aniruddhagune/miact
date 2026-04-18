import sys
import asyncio

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
from fastapi.responses import JSONResponse
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

@app.get("/")
def root():
    return {"message": "MIACT API is running", "status": "online"}

@app.get("/favicon.ico")
def favicon():
    return {}

# Include Routers
app.include_router(query.router)
app.include_router(search.router)
app.include_router(debug.router)
app.include_router(config.router)
