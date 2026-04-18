import sys
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# ---- Windows Asyncio Fix ----
# Required for Playwright/Subprocess to work on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from backend.routes import query, search, debug, config
from backend.database.schema_manager import initialize_db
from backend.utils.logger import logger

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
