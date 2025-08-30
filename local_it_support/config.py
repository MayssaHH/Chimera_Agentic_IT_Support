"""Configuration settings for Local IT Support."""

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
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
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
