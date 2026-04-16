from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    model_name:str
    message:str
    chat_id:Optional[str]=None

class ChatResponse(BaseModel):
    reply:str

class Chat(BaseModel):
    role:str
    content:str

class Query(BaseModel):
    query:str