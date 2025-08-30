"""LLM Registry for Local IT Support."""

from typing import Literal, Optional
from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models.llms import LLM

from ..config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        """Get a chat model instance."""
        pass
    
    @abstractmethod
    def get_llm(self, model_name: str) -> LLM:
        """Get an LLM instance."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        """Get an Ollama chat model."""
        return ChatOllama(
            base_url=self.base_url,
            model=model_name,
            temperature=0.1
        )
    
    def get_llm(self, model_name: str) -> LLM:
        """Get an Ollama LLM."""
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=self.base_url,
            model=model_name,
            temperature=0.1
        )


class VLLMProvider(LLMProvider):
    """vLLM provider."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        """Get a vLLM chat model."""
        # Note: vLLM integration would need langchain-vllm package
        # For now, using ChatOpenAI as a placeholder
        return ChatOpenAI(
            base_url=f"{self.base_url}/v1",
            model=model_name,
            temperature=0.1,
            api_key="dummy"  # vLLM doesn't require API key
        )
    
    def get_llm(self, model_name: str) -> LLM:
        """Get a vLLM LLM."""
        # Placeholder implementation
        from langchain_openai import OpenAI
        return OpenAI(
            base_url=f"{self.base_url}/v1",
            model=model_name,
            temperature=0.1,
            api_key="dummy"
        )


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
    
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        """Get an OpenRouter chat model."""
        return ChatOpenAI(
            base_url=self.base_url,
            model=model_name,
            temperature=0.1,
            api_key=self.api_key
        )
    
    def get_llm(self, model_name: str) -> LLM:
        """Get an OpenRouter LLM."""
        from langchain_openai import OpenAI
        return OpenAI(
            base_url=self.base_url,
            model=model_name,
            temperature=0.1,
            api_key=self.api_key
        )


class LLMRegistry:
    """Registry for managing LLM instances."""
    
    def __init__(self):
        self._providers = {}
        self._chat_models = {}
        self._llms = {}
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup available LLM providers."""
        if settings.llm_provider == "ollama":
            self._providers["ollama"] = OllamaProvider(settings.ollama_base_url)
        elif settings.llm_provider == "vllm":
            self._providers["vllm"] = VLLMProvider(settings.vllm_base_url)
        elif settings.llm_provider == "openrouter":
            self._providers["openrouter"] = OpenRouterProvider(
                settings.openrouter_base_url, 
                settings.openrouter_api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    def get_provider(self) -> LLMProvider:
        """Get the current LLM provider."""
        provider_name = settings.llm_provider
        if provider_name not in self._providers:
            raise ValueError(f"Provider {provider_name} not configured")
        return self._providers[provider_name]
    
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        """Get a chat model by name."""
        cache_key = f"{settings.llm_provider}:{model_name}"
        if cache_key not in self._chat_models:
            provider = self.get_provider()
            self._chat_models[cache_key] = provider.get_chat_model(model_name)
        return self._chat_models[cache_key]
    
    def get_llm(self, model_name: str) -> LLM:
        """Get an LLM by name."""
        cache_key = f"{settings.llm_provider}:{model_name}"
        if cache_key not in self._llms:
            provider = self.get_provider()
            self._llms[cache_key] = provider.get_llm(model_name)
        return self._llms[cache_key]


# Global LLM registry instance
llm_registry = LLMRegistry()


def get_llm(role: Literal["classifier", "planner", "it", "router"]) -> BaseChatModel:
    """
    Get an LLM for a specific role.
    
    Args:
        role: The role for which to get the LLM
        
    Returns:
        A LangChain chat model configured for the role
        
    Raises:
        ValueError: If the role is not supported
    """
    if role == "classifier":
        return llm_registry.get_chat_model(settings.classifier_model)
    elif role == "planner":
        return llm_registry.get_chat_model(settings.planner_model)
    elif role == "it":
        return llm_registry.get_chat_model(settings.it_model)
    elif role == "router":
        return llm_registry.get_chat_model(settings.router_model)
    else:
        raise ValueError(f"Unsupported role: {role}")


def get_escalation_llm() -> BaseChatModel:
    """
    Get the escalation LLM (higher capability model).
    
    Returns:
        A LangChain chat model for escalation scenarios
    """
    return llm_registry.get_chat_model(settings.escalation_model)


def switch_provider(provider: Literal["ollama", "vllm", "openrouter"]):
    """
    Switch the LLM provider.
    
    Args:
        provider: The new provider to use
    """
    global llm_registry
    settings.llm_provider = provider
    llm_registry = LLMRegistry()

