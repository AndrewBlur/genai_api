from fastapi import FastAPI,Depends
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router

app = FastAPI(tags=["Home"])

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return "hello world"

