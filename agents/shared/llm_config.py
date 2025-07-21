"""
LLM Configuration for Hospital Agent Platform
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from typing import Optional

from backend.config import settings


class LLMConfig:
    """LLM configuration and initialization"""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.model_name = settings.llm_model
        self.provider = settings.llm_provider
        
    def get_llm(self, temperature: float = 0.3, max_tokens: Optional[int] = 1200) -> BaseChatModel:
        """Get configured LLM instance with optimized settings for Gemini 2.5 Flash"""
        if self.provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.model_name,  # gemini-2.5-flash (real Gemini 2.5 Flash)
                google_api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                convert_system_message_to_human=True
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def get_embedding_model(self):
        """Get embedding model for RAG"""
        # For now, we'll use sentence transformers
        # This can be extended to use Google's embedding models
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')


# Global LLM config instance
llm_config = LLMConfig()
