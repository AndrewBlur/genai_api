from fastapi import HTTPException,status

import json
from uuid import uuid4
from typing import Optional

from app.models.chats import ChatResponse
from app.utils.groq import call_groq
from app.utils.tools import get_time,search,rag
from app.services.dbservices import get_chat,update_chat_history,create_chat,update_chat_tokens

## all tools
available_tools = {"get_time":get_time, "search":search, "rag":rag}

def execute_tool_call(tool_call,user_id:Optional[str]):
    function_name = tool_call["function"]["name"]
    function_to_call = available_tools[function_name]
    function_args = json.loads(tool_call["function"]["arguments"])
    if function_name == "rag":
        function_args["user_id"] = user_id
    return function_to_call(**function_args)


def chat_with_llm(model_name:str,message:str,chat_id:str,user_id:str)->ChatResponse:
    messages = [] ## buffer
    if chat_id:
    ## restore the message of the chatid
        chat = get_chat(chat_id)
        if chat.get("tokens")<110000:
            messages = chat["chat_history"]
            user_message = {"role":"user","content":message}

            messages.append(user_message) 
            update_chat_history(chat_id,user_message)

        else:
            raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="context window exceeded")   
    else:
        chat_id = str(uuid4())
        user_message = {"role":"user","content":message}

        messages.append(user_message)
        create_chat(chat_id,messages,0)        
    
    
    response = call_groq(messages,model_name)

    assistant_message = response["choices"][0]["message"]

    messages.append(assistant_message)
    update_chat_history(chat_id,assistant_message)

    while "tool_calls" in assistant_message:
        for tool_call in assistant_message["tool_calls"]:
            tool_id = tool_call["id"]
            tool_answer = execute_tool_call(tool_call,user_id)
            tool_message = {
                "role":"tool",
                "tool_call_id":tool_id,
                "name":tool_call["function"]["name"],
                "content":str(tool_answer)
            }

            messages.append(tool_message)
            update_chat_history(chat_id,tool_message)

        response = call_groq(messages,model_name)

        assistant_message = response["choices"][0]["message"]
        
        messages.append(assistant_message)
        update_chat_history(chat_id,assistant_message)

    total_tokens_used = response["usage"]["total_tokens"]
    update_chat_tokens(chat_id,total_tokens_used)

    return assistant_message

