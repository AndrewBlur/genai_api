from fastapi import APIRouter,Depends,HTTPException,Form,File,UploadFile
from app.dependencies.auth import get_current_user
from app.models.chats import ChatRequest
from app.models.users import User
from app.services.llmservices import chat_with_llm
from typing import Annotated,List

router = APIRouter(tags=["chatbot"])

@router.post("/chat")
def chat(query:ChatRequest,user = Depends(get_current_user)):
    model_name = query.model_name
    message = query.message
    chat_id = query.chat_id
    try:
        response = chat_with_llm(model_name,message,chat_id)
        return response
    except HTTPException:
        raise

@router.post("/store")
async def create_upload(            
    file: Annotated[UploadFile, File()],
    user:User = Depends(get_current_user) # <--- Fixed the syntax here
):
    
    
    return {
        "file_name": file.filename,
        "user": user
    }