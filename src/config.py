"""Configuration settings for Local IT Support."""

from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # JIRA Configuration
    jira_base_url: str
    jira_user: str
    jira_token: str
    
    # SMTP Configuration
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    
    # LLM Provider Configuration
    llm_provider: Literal["ollama", "vllm", "openrouter"] = "ollama"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # vLLM Configuration
    vllm_base_url: str = "http://localhost:8000"
    
    # OpenRouter Configuration
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Model Configuration
    classifier_model: str = "llama3.1:8b"
    planner_model: str = "mistral:7b"
    it_model: str = "llama3.1:8b"
    router_model: str = "mistral:7b"
    escalation_model: str = "mixtral:8x7b"
    
    # LLM Configuration
    classifier_temperature: float = 0.2
    classifier_max_tokens: int = 1000
    planner_temperature: float = 0.3
    planner_max_tokens: int = 2000
    it_temperature: float = 0.2
    it_max_tokens: int = 1000
    router_temperature: float = 0.2
    router_max_tokens: int = 1000
    escalation_temperature: float = 0.4
    escalation_max_tokens: int = 3000
    
    # Retry Configuration
    llm_max_retries: int = 3
    llm_retry_delay_base: float = 1.0
    llm_retry_delay_max: float = 10.0
    
    # Database Configuration
    database_url: str = "sqlite:///./local_it_support.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
