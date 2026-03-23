from fastapi import FastAPI
from backend.routes import query
from backend.routes import search


app = FastAPI()

app.include_router(query.router)
app.include_router(search.router)
