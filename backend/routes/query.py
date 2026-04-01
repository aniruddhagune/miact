from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.query_parser import parse_query

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/parse")
def parse(req: QueryRequest):
    return parse_query(req.query)