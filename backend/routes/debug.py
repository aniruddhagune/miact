from fastapi import APIRouter
from pydantic import BaseModel
import backend.config.variables as _vars

router = APIRouter()


class DebugPayload(BaseModel):
    debug: bool


@router.post("/api/debug")
def set_debug_mode(payload: DebugPayload):
    """Toggle DEBUG flag at runtime without restarting the server."""
    _vars.DEBUG = payload.debug
    return {"debug": _vars.DEBUG}


@router.get("/api/debug")
def get_debug_mode():
    return {"debug": _vars.DEBUG}
