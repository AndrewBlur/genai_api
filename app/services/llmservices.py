from app.models.chats import ChatResponse
from app.utils.groq import call_groq

def chat_with_llm(model_name:str,message:str,chat_id:str)->ChatResponse:
   
    ## restore the message of the chatid
    messages = [{"role":"user","content":message}]
    response = call_groq(messages,model_name)
    
    return response