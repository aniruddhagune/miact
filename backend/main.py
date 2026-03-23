from fastapi import FastAPI
from backend.routes import query

app = FastAPI()

app.include_router(query.router)