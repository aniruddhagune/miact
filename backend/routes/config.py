from fastapi import APIRouter
from backend.config.unified_config import get_unified_config

router = APIRouter()

@router.get("/config/groups")
def fetch_config_groups():
    """Returns the unified categorization groups for both tech and general domains."""
    return get_unified_config()
