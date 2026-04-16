from app.db.client import db
from pymongo.operations import SearchIndexModel

users_collection = db["users"]
chats_collection = db["chats"]
knowledgestore_collection = db["knowledgestore"]

## Indexs
search_index_model = SearchIndexModel(
    definition= {
        "fields":[
            {"type":"vector",
             "path":"embeddings",
             "numDimensions":256,
             "similarity":"cosine",
             "quantization":"scalar"},
             {
                 "type":"filter",
                 "path":"userid"
             }
        ]
    },
    name="vector-index",
    type="vectorSearch"
)