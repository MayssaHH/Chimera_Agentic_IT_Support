"""Configuration for the ingestion pipeline."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class IngestionConfig(BaseSettings):
    """Configuration for document ingestion."""
    
    # OpenAI settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # Vector store settings
    storage_path: str = Field(default="./storage/vectorstore", env="VECTOR_STORE_PATH")
    store_type: str = Field(default="chromadb", env="VECTOR_STORE_TYPE")
    
    # Chunking settings
    max_tokens: int = Field(default=800, env="MAX_CHUNK_TOKENS")
    overlap_tokens: int = Field(default=120, env="OVERLAP_TOKENS")
    
    # Document processing settings
    supported_extensions: set = Field(
        default={".pdf", ".docx", ".txt"},
        env="SUPPORTED_EXTENSIONS"
    )
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def storage_path_obj(self) -> Path:
        """Get storage path as Path object."""
        return Path(self.storage_path)
    
    def ensure_storage_directory(self) -> None:
        """Ensure the storage directory exists."""
        self.storage_path_obj.mkdir(parents=True, exist_ok=True)


# Default configuration instance
config = IngestionConfig()
