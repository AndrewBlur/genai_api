from app.db.collections import users_collection
from fastapi import HTTPException,status
from app.core.security import hashpwd

def create_user(username:str,pwd:str):
    user = get_user(username)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="user exists")

    hashed_pwd = hashpwd(pwd)
    user = users_collection.insert_one({"username":username,"password":hashed_pwd})
    return {"id":str(user.inserted_id),"username":username}

def get_user(username:str):
    user = users_collection.find_one({"username":username})

    if not user:
        return None

    return { "id" : str(user["_id"]), "username" : user["username"] , "password" : user["password"]}