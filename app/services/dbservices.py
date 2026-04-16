from fastapi import HTTPException,status,File,Depends

from typing import List
import os

from nomic import embed

from datetime import timezone,timedelta,datetime
from app.models.users import User
from app.db.collections import users_collection,chats_collection,knowledgestore_collection,search_index_model
from app.db.client import db
from app.core.security import hashpwd
from app.models.chats import Chat

collections = {"users":users_collection,"chats":chats_collection,"knowledgestore":knowledgestore_collection}


def startDB():
    existing_collections = db.list_collection_names()
    ## Create all collections
    for collection in collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            print("Created "+collection+" Collection")
        else:
            print(collection+" Collection already exists")

    ## Create all index
    import time
    try:
        result = knowledgestore_collection.create_search_index(model=search_index_model)
        print(f"Search Index creation request submitted: {result}")
        
        # 5. Optional: Wait for the index to be ready
        print("Waiting for Search index to build...")
        while True:
            indices = list(knowledgestore_collection.list_search_indexes(name="vector-index"))
            if indices and indices[0].get("queryable"):
                print("Index is now queryable!")
                break
            time.sleep(2)
            
    except Exception as e:
        print(f"Error creating Search index: {e}")
    
    ## Creating TTL index
    print("Creating TTL Index")
    knowledgestore_collection.create_index(
    "expireAt",
    expireAfterSeconds=0)


## Users Collection Operations
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

## Chats Collection operations 
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

