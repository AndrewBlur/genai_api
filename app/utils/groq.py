import requests
from typing import List
import json

from app.core.settings import LLMSettings
from app.models.chats import Chat
from app.utils.tools import tool_schema

llm_settings = LLMSettings()

headers = {"Content-Type":"application/json","Authorization":f"Bearer {llm_settings.GROQ_API_KEY}"}



def call_groq(messages:List[Chat],model_name:str):
    payload = {"model":model_name,
               "messages":messages,
               "tools":tool_schema}
    
    
    response = requests.post(url=llm_settings.CHAT_COMPLETION_URL,json=payload,headers=headers)
    data = json.loads(response.text)

    return data
