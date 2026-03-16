from app.services.dbservices import get_user
from fastapi import HTTPException,status
from app.core.security import checkpwd,create_token

def login_user(username:str,password:str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Username or Password")
    if not checkpwd(password,user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Username or Password")
    token = create_token({"sub":username})

    return {"access_token":token,"token_type":"bearer"}

