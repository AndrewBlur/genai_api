from fastapi import APIRouter,Depends,HTTPException,Form,File,UploadFile,status
from app.dependencies.auth import get_current_user
from app.models.chats import ChatRequest,Query
from app.models.users import User
from app.services.llmservices import chat_with_llm
from app.services.ragservices import store_in_knowledgestore,retrieve_from_knowledgestore
from typing import Annotated,List
import os
import io
from app.utils.loadpdf import load_pdf
import docx2txt 
router = APIRouter(tags=["chatbot"])

@router.post("/chat")
def chat(query:ChatRequest,user = Depends(get_current_user)):
    model_name = query.model_name
    message = query.message
    chat_id = query.chat_id
    try:
        response = chat_with_llm(model_name,message,chat_id,user["id"])
        return response
    except HTTPException:
        raise

@router.post("/store")
async def store(            
    file: Annotated[UploadFile, File()],
    user:User = Depends(get_current_user)
):
    contents = await file.read()
    
    processed_contents = ""
    _, ext = os.path.splitext(file.filename)

    if ext.lower() == ".txt":
        try:
            processed_contents = contents.decode("utf-8")
        except:
            raise HTTPException(status_code=400, detail="Invalid text encoding")
    elif ext.lower() == ".pdf":
        processed_contents = load_pdf(contents)
    elif ext.lower() == ".md":
        processed_contents = contents.decode("utf-8")
    elif ext.lower() == ".docx":
        docx_file = io.BytesIO(contents)
        processed_contents = docx2txt.process(docx_file)
    else:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="Not supported")
    
    store_in_knowledgestore(file.filename,processed_contents,user["id"])

    return {
        "file_name": file.filename,
        "user": user["id"]
    }

@router.post("/retrieve")
def retrieve(query:Query,user:User = Depends(get_current_user)):
    chunks = retrieve_from_knowledgestore(query.query,user["id"])
    return chunks