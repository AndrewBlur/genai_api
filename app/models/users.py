from pydantic import BaseModel


class UserCreate(BaseModel):
    username:str
    password:str
    
class User(BaseModel):
    id:str
    username:str
    password:str

    