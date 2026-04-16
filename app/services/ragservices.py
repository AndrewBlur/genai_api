from fastapi import HTTPException,status,File,Depends

from typing import List
import os

from nomic import embed

from datetime import timezone,timedelta,datetime

from app.dependencies.auth import get_current_user
from app.models.users import User
from app.db.collections import knowledgestore_collection

def create_chunks(data):
    knowledgestore_collection.insert_many(data)

def store_in_knowledgestore(filename:str,content:str,user_id:str):
    
    ## chunking strategy
    n = len(content)
    chunk_overlap = 150
    chunk_size = 1500
    chunks = [content[i*chunk_size-chunk_overlap:(i+1)*chunk_size]  for i in range(1,n//chunk_size)]
    chunks.append(content[0:chunk_size])

    ##embed the chunks
    nomic_res = embed.text(chunks,model="nomic-embed-text-v1.5",task_type='search_document',
    dimensionality=256)
    embeddings = nomic_res["embeddings"]

    data = [{"filename":filename,"text":chunks[i],"embeddings":embeddings[i],"userid":user_id,"expireAt":datetime.now(timezone.utc) + timedelta(seconds=1800)} for i in range(0,len(embeddings))]
    create_chunks(data)

    print("filename",filename)
    print("content",content)
    print("user_id",user_id)

def retrieve_from_knowledgestore(query:str,user_id:str,max_results:int=5,):
    embeddings = embed.text([query],model="nomic-embed-text-v1.5",task_type='search_query',
    dimensionality=256)
    qe = embeddings["embeddings"][0]
    res = knowledgestore_collection.aggregate([
    {
        "$vectorSearch":{
            "index":"vector-index",
            "path":"embeddings",
            "queryVector":qe,
            "numCandidates":100,
            "limit":max_results,
            "filter":{"userid":user_id}
        }
        },
        {       
            "$project": {
            "text": 1,
            "filename":1,
            "score": {"$meta": "vectorSearchScore"}
        }
    }])
    chunks = []
    for doc in res:
        doc.update({"_id":str(doc["_id"])})
        chunks.append(doc)

    return chunks