from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.models.users import UserCreate
from app.services.dbservices import create_user
from app.services.authservices import login_user


router = APIRouter(tags=["auth"])

@router.post("/register")
def register(user: UserCreate):
    try:
        return create_user(user.username,user.password)
    except HTTPException:
        raise

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    try:
        return login_user(form.username,form.password)
    except HTTPException:
        raise

