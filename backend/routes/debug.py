from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import backend.config.variables as _vars

router = APIRouter()


class DebugSettings(BaseModel):
    debug: bool
    services: List[str]
    log_all: bool


@router.post("/debug/settings")
def update_debug_settings(settings: DebugSettings):
    """Update debug configurations at runtime."""
    _vars.DEBUG = settings.debug
    # Ensure services are uppercase for matching in logger
    _vars.DEBUG_SERVICES = [s.upper() for s in settings.services]
    _vars.LOG_ALL_TO_FILE = settings.log_all
    
    return get_current_settings()


@router.get("/debug/settings")
def get_current_settings():
    return {
        "debug": _vars.DEBUG,
        "services": _vars.DEBUG_SERVICES,
        "log_all": _vars.LOG_ALL_TO_FILE,
        "available_services": [
            "SEARCH", "PARSER", "DATABASE", "NLP", "EXTRACTOR", 
            "PIPELINE", "PROCESSING", "ORCHESTRATOR", "SYSTEM", 
            "RESOLVER", "SCRAPER"
        ]
    }

# Legacy endpoint for backward compatibility
@router.get("/debug")
def get_debug_mode():
    return {"debug": _vars.DEBUG}

@router.post("/debug")
def set_debug_mode(payload: dict):
    _vars.DEBUG = payload.get("debug", _vars.DEBUG)
    return {"debug": _vars.DEBUG}
