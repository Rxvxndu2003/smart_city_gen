"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Get the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    APP_NAME: str = "Smart City Planning System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = []
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    
    # Google Maps
    GOOGLE_MAPS_API_KEY: str
    
    # Blender
    BLENDER_EXECUTABLE_PATH: str = "/usr/local/bin/blender"
    BLENDER_SCRIPTS_DIR: str = "./blender_scripts"
    
    # Meshy AI API
    MESHY_API_KEY: Optional[str] = None
    
    # Replicate API
    REPLICATE_API_TOKEN: Optional[str] = None

    # CubiCasa API
    CUBICASA_API_KEY: Optional[str] = None
    
    # ModelsLab API (3D Floor Plan Generation)
    MODELSLAB_API_KEY: Optional[str] = None
    
    # GetFloorPlan AI API (Professional 3D Floor Plan & 360° Tour Generation)
    GETFLOORPLAN_AUTH_TOKEN: Optional[str] = None
    GETFLOORPLAN_CRM_TAG_ID: Optional[int] = None
    GETFLOORPLAN_DOMAIN: str = "https://backend.estate.hart-digital.com"
    
    # Cloudinary Configuration (Cloud Image Storage)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    
    # File Storage
    STORAGE_BASE_PATH: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # ML Models
    ML_MODELS_DIR: str = "./ml_models"
    DEPLOYED_MODEL_PATH: str = "./ml_models/deployed_model.pt"
    CLF_OPEN_SPACE_PATH: str = "./ml_models/clf_requires_open_space.pkl"
    REG_OPEN_SPACE_PATH: str = "./ml_models/reg_min_open_space_m2.pkl"
    FEATURE_COLUMNS_PATH: str = "./ml_models/feature_columns.json"
    
    # Blockchain Integration
    ETHEREUM_RPC_URL: Optional[str] = None  # e.g., https://sepolia.infura.io/v3/YOUR_API_KEY
    ETHEREUM_CONTRACT_ADDRESS: Optional[str] = None  # Deployed smart contract address
    ETHEREUM_PRIVATE_KEY: Optional[str] = None  # Server wallet private key (keep secret!)
    
    # IPFS Configuration
    IPFS_GATEWAY_URL: str = "https://ipfs.io/ipfs/"
    IPFS_API_URL: str = "http://localhost:5001"  # Local IPFS node
    PINATA_API_KEY: Optional[str] = None
    PINATA_SECRET_KEY: Optional[str] = None
    WEB3_STORAGE_TOKEN: Optional[str] = None
    
    # Email (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@smartcity.lk"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        return []
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return self.CORS_ORIGINS


# Global settings instance
settings = Settings()
