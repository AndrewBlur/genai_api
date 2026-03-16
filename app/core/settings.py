from pydantic_settings import BaseSettings,SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()

class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env")

    DB_CONN_STR:str
    DB_NAME:str


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env")

    ALGORITHM:str
    TIME_TO_EXPIRE:int
    SECRET_KEY:str

class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env")

    GROQ_API_KEY:str
    CHAT_COMPLETION_URL:str
