"""
Configuration settings for the Hospital Agent Platform
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Hospital Operations & Logistics Agentic Platform"
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://postgres:hospital123@localhost:5432/hospital_ops"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_hosts: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Vector Database
    vector_db_path: str = "./data/vector_store"
    chroma_persist_directory: str = "./data/chroma_db"
    
    # LLM Configuration
    google_api_key: str = "AIzaSyCrEfICW4RYyJW45Uy0ZSduXVKUKjNu25I"
    llm_model: str = "gemini-2.0-flash-exp"
    llm_provider: str = "google"
    
    # MCP Server
    mcp_server_port: int = 3001
    
    # Agent Configuration
    max_agent_retries: int = 3
    agent_timeout: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
