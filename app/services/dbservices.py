from fastapi import HTTPException,status

from typing import List

from app.db.collections import users_collection,chats_collection
from app.core.security import hashpwd
from app.models.chats import Chat


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


def create_chat(chat_id:str,messages:List[Chat],tokens:int):
    chats_collection.insert_one({"chat_id":chat_id,"chat_history":messages,"tokens":tokens})


def get_chat(chat_id:str):
    chat = chats_collection.find_one({"chat_id":chat_id})
    if not chat:
        return None
    return {"chat_id":chat["chat_id"],"chat_history":chat["chat_history"],"tokens":chat["tokens"]}


def update_chat_history(chat_id:str,message:Chat):
    filter_query = {"chat_id":chat_id}
    update_operation = {"$push": {"chat_history":message}}
    chats_collection.update_one(filter_query,update_operation)



def update_chat_tokens(chat_id:str,tokens:int):
    filter_query = {"chat_id":chat_id}
    update_operation = {"$set":{"tokens":tokens}}
    chats_collection.update_one(filter_query,update_operation)
