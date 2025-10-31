from pydantic_settings import BaseSettings
from typing import Optional, List
import json

class Settings(BaseSettings):
    # API
    PROJECT_NAME: str = "Greenhouse IoT Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_KEEPALIVE: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: str = '["http://167.86.89.98:3000","http://localhost:3000","http://127.0.0.1:3000"]'
    
    @property
    def cors_origins(self) -> List[str]:
        return json.loads(self.BACKEND_CORS_ORIGINS)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
