from fastapi import HTTPException,status
from fastapi.security import OAuth2PasswordBearer

import bcrypt
from jose import jwt,JWTError

from datetime import datetime,timedelta

from app.core.settings import JWTSettings


jwt_settings = JWTSettings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hashpwd(pwd:str):
    return bcrypt.hashpw(pwd.encode(),bcrypt.gensalt()).decode()

def checkpwd(pwd:str,hashed_pwd:str):
    return bcrypt.checkpw(pwd.encode(),hashed_password=hashed_pwd.encode())

def create_token(data:dict):
    payload = data.copy()
    payload.update({"exp":datetime.now()+timedelta(minutes=jwt_settings.TIME_TO_EXPIRE)})
    return jwt.encode(payload,jwt_settings.SECRET_KEY,jwt_settings.ALGORITHM)

def decode_token(token:str):
    try:
        payload = jwt.decode(token,jwt_settings.SECRET_KEY,jwt_settings.ALGORITHM)
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Token")
    
