from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, Field


class Settings(BaseSettings):
    # 基本设置
    PROJECT_NAME: str = "Yili AI Python API"
    PROJECT_DESCRIPTION: str = "基于 FastAPI 的 Python 项目"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # 服务器设置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # CORS设置
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["http://localhost", "http://localhost:8000", "http://localhost:3000"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库设置
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Elasticsearch设置
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    
    # DeepSeek设置
    DEEPSEEK_API_KEY: str = Field(default="")
    
    # 通义千问设置
    DASHSCOPE_API_KEY: str = Field(default="")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()