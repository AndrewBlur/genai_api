from fastapi import FastAPI,Depends
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.services.dbservices import startDB
from app.db.client import close_client
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    startDB()
    yield
    close_client()

app = FastAPI(lifespan=lifespan,tags=["Home"])

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return "hello world"

