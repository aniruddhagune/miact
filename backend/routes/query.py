from fastapi import APIRouter
from backend.services.query_parser import parse_query

router = APIRouter()

@router.get("/parse")
def parse(query: str):
    return parse_query(query)