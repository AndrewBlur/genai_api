from fastapi import FastAPI,Depends
from app.routes.auth import router as auth_router
from app.dependencies.auth import get_current_user

app = FastAPI()

app.include_router(auth_router)

@app.get("/")
def root():
    return "hello world"

@app.get("/protected")
def pro_route(user = Depends(get_current_user)):
    return user
