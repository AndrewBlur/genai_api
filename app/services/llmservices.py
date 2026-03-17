from app.models.chats import ChatResponse
from app.utils.groq import call_groq
from uuid import uuid4
from app.services.dbservices import get_chat,update_chat_history,create_chat,update_chat_tokens
from fastapi import HTTPException,status

def chat_with_llm(model_name:str,message:str,chat_id:str)->ChatResponse:

    if chat_id:
    ## restore the message of the chatid
        chat = get_chat(chat_id)
        if chat.get("tokens")<110000:
            messages = chat["chat_history"]
            messages.append({"role":"user","content":message})
        else:
            raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="context window exceeded")
         
    else:
        chat_id = str(uuid4())
        messages = [{"role":"user","content":message}]
        
    response = call_groq(messages,model_name)

    tokens = response["usage"]["total_tokens"]
    assistant_message = response["choices"][0]["message"]

    chat = get_chat(chat_id)
    if not chat:
        create_chat(chat_id,[{"role":"user","content":message},assistant_message],tokens)
    else:
        update_chat_history(chat_id,{"role":"user","content":message})
        update_chat_history(chat_id,assistant_message)
        update_chat_tokens(chat_id,tokens)

    return assistant_message