from app.dependencies.auth import get_current_user
from fastapi import APIRouter,Depends,HTTPException
from app.models.chats import ChatRequest,ChatResponse
from app.services.llmservices import chat_with_llm
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

