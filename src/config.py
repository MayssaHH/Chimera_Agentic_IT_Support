"""
Configuration settings for IT Support System

This file provides default configuration values for the system to work
without requiring external services during testing.
"""

import os
from typing import Optional

class Settings:
    """Application settings with sensible defaults"""
    
    # JIRA Configuration (using mock for testing)
    jira_base_url: str = ""
    jira_user: str = ""
    jira_token: str = ""
    jira_project_key: str = "IT"
    
    # SMTP Configuration (using mock for testing)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    
    # LLM Provider Configuration
    llm_provider: str = "ollama"  # Options: ollama, openai, local
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # OpenAI Configuration (if using OpenAI)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Model Configuration
    classifier_model: str = "llama3.1:8b"
    planner_model: str = "mistral:7b"
    it_model: str = "llama3.1:8b"
    router_model: str = "mistral:7b"
    
    # Database Configuration
    database_url: str = "sqlite:///./it_support.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Workflow Configuration
    use_mock_services: bool = False  # NO MOCKS ALLOWED!
    enable_persistence: bool = False
    max_workflow_iterations: int = 50
    workflow_timeout_seconds: int = 3600
    
    def __init__(self):
        # Load from environment variables if available
        self.jira_base_url = os.getenv("JIRA_BASE_URL", self.jira_base_url)
        self.jira_user = os.getenv("JIRA_USER", self.jira_user)
        self.jira_token = os.getenv("JIRA_TOKEN", self.jira_token)
        self.jira_project_key = os.getenv("JIRA_PROJECT_KEY", self.jira_project_key)
        
        self.smtp_host = os.getenv("SMTP_HOST", self.smtp_host)
        self.smtp_port = int(os.getenv("SMTP_PORT", self.smtp_port))
        self.smtp_user = os.getenv("SMTP_USER", self.smtp_user)
        self.smtp_password = os.getenv("SMTP_PASSWORD", self.smtp_password)
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.ollama_base_url)
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.api_host = os.getenv("API_HOST", self.api_host)
        self.api_port = int(os.getenv("API_PORT", self.api_port))
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        self.use_mock_services = os.getenv("USE_MOCK_SERVICES", "true").lower() == "true"
        self.enable_persistence = os.getenv("ENABLE_PERSISTENCE", "false").lower() == "true"
        self.max_workflow_iterations = int(os.getenv("MAX_WORKFLOW_ITERATIONS", self.max_workflow_iterations))
        self.workflow_timeout_seconds = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", self.workflow_timeout_seconds))

# Global settings instance
settings = Settings()
