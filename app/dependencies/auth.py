from fastapi import Depends,HTTPException,status
from app.core.security import oauth2_scheme,decode_token
from app.services.dbservices import get_user

def get_current_user(token:str=Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)    
    except HTTPException:
        raise 

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid payload")
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user not found")
    return user
