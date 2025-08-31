"""LLM Registry for Local IT Support with JSON Schema and Function Calling."""

import json
import logging
from typing import Literal, Optional, Dict, Any, Type, Union, List
from abc import ABC, abstractmethod
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models.llms import LLM
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_function
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_chat_model(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> BaseChatModel:
        """Get a chat model instance with specified parameters."""
        pass
    
    @abstractmethod
    def get_llm(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> LLM:
        """Get an LLM instance with specified parameters."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_chat_model(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> BaseChatModel:
        """Get an Ollama chat model."""
        return ChatOllama(
            base_url=self.base_url,
            model=model_name,
            temperature=temperature,
            # Ollama doesn't support max_tokens in the same way
            # but we can use stop sequences or other methods
        )
    
    def get_llm(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> LLM:
        """Get an Ollama LLM."""
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=self.base_url,
            model=model_name,
            temperature=temperature,
        )


class VLLMProvider(LLMProvider):
    """vLLM provider."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_chat_model(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> BaseChatModel:
        """Get a vLLM chat model."""
        return ChatOpenAI(
            base_url=f"{self.base_url}/v1",
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key="dummy"  # vLLM doesn't require API key
        )
    
    def get_llm(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> LLM:
        """Get a vLLM LLM."""
        from langchain_openai import OpenAI
        return OpenAI(
            base_url=f"{self.base_url}/v1",
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key="dummy"
        )


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
    
    def get_chat_model(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> BaseChatModel:
        """Get an OpenRouter chat model."""
        return ChatOpenAI(
            base_url=self.base_url,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key
        )
    
    def get_llm(self, model_name: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> LLM:
        """Get an OpenRouter LLM."""
        from langchain_openai import OpenAI
        return OpenAI(
            base_url=self.base_url,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key
        )


class StructuredLLMClient:
    """Client for making structured LLM calls with JSON schema validation and retries."""
    
    def __init__(self, llm: BaseChatModel, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ValidationError, json.JSONDecodeError, Exception))
    )
    async def call_with_json_schema(
        self, 
        prompt: str, 
        input_data: Dict[str, Any], 
        response_schema: Type[BaseModel],
        system_message: Optional[str] = None
    ) -> BaseModel:
        """
        Call LLM with JSON schema validation and automatic retries.
        
        Args:
            prompt: The prompt template or system message
            input_data: Input data for the prompt
            response_schema: Pydantic model for response validation
            system_message: Optional system message override
            
        Returns:
            Validated response as Pydantic model
            
        Raises:
            ValidationError: If response doesn't match schema
            Exception: If LLM call fails after retries
        """
        try:
            # Create prompt template
            if system_message:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("human", prompt)
                ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", prompt),
                    ("human", "{input_data}")
                ])
            
            # Create JSON output parser
            json_parser = JsonOutputParser(pydantic_object=response_schema)
            
            # Create the chain
            chain = prompt_template | self.llm | json_parser
            
            # Execute with retries
            for attempt in range(self.max_retries):
                try:
                    if system_message:
                        result = await chain.ainvoke({"input_data": json.dumps(input_data, indent=2)})
                    else:
                        result = await chain.ainvoke({"input_data": json.dumps(input_data, indent=2)})
                    
                    # Validate against schema
                    validated_result = response_schema(**result)
                    logger.info(f"LLM call successful on attempt {attempt + 1}")
                    return validated_result
                    
                except (ValidationError, json.JSONDecodeError) as e:
                    logger.warning(f"Attempt {attempt + 1} failed with validation error: {e}")
                    if attempt == self.max_retries - 1:
                        raise ValidationError(f"Failed to get valid response after {self.max_retries} attempts: {e}")
                    continue
                    
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                    if attempt == self.max_retries - 1:
                        raise e
                    continue
            
            raise Exception(f"Failed to get valid response after {self.max_retries} attempts")
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def call_with_function_calling(
        self,
        prompt: str,
        input_data: Dict[str, Any],
        tools: List[BaseTool],
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call LLM with function calling and automatic retries.
        
        Args:
            prompt: The prompt template or system message
            input_data: Input data for the prompt
            tools: List of tools for function calling
            system_message: Optional system message override
            
        Returns:
            Function call results
            
        Raises:
            Exception: If LLM call fails after retries
        """
        try:
            # Convert tools to OpenAI function format
            functions = [convert_to_openai_function(tool) for tool in tools]
            
            # Create prompt template
            if system_message:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("human", prompt)
                ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", prompt),
                    ("human", "{input_data}")
                ])
            
            # Create the chain with function calling
            chain = prompt_template | self.llm.bind(functions=functions)
            
            # Execute with retries
            for attempt in range(self.max_retries):
                try:
                    if system_message:
                        result = await chain.ainvoke({"input_data": json.dumps(input_data, indent=2)})
                    else:
                        result = await chain.ainvoke({"input_data": json.dumps(input_data, indent=2)})
                    
                    logger.info(f"LLM call with function calling successful on attempt {attempt + 1}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                    if attempt == self.max_retries - 1:
                        raise e
                    continue
            
            raise Exception(f"Failed to get valid response after {self.max_retries} attempts")
            
        except Exception as e:
            logger.error(f"LLM call with function calling failed: {e}")
            raise


class LLMRegistry:
    """Registry for managing LLM instances with role-specific configurations."""
    
    def __init__(self):
        self._providers = {}
        self._chat_models = {}
        self._llms = {}
        self._structured_clients = {}
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
    
    def get_chat_model(self, model_name: str, role: str = "default") -> BaseChatModel:
        """Get a chat model by name with role-specific configuration."""
        cache_key = f"{settings.llm_provider}:{model_name}:{role}"
        if cache_key not in self._chat_models:
            provider = self.get_provider()
            
            # Configure based on role
            temperature, max_tokens = self._get_role_config(role)
            
            self._chat_models[cache_key] = provider.get_chat_model(
                model_name, 
                temperature=temperature, 
                max_tokens=max_tokens
            )
        return self._chat_models[cache_key]
    
    def get_llm(self, model_name: str, role: str = "default") -> LLM:
        """Get an LLM by name with role-specific configuration."""
        cache_key = f"{settings.llm_provider}:{model_name}:{role}"
        if cache_key not in self._llms:
            provider = self.get_provider()
            
            # Configure based on role
            temperature, max_tokens = self._get_role_config(role)
            
            self._llms[cache_key] = provider.get_llm(
                model_name, 
                temperature=temperature, 
                max_tokens=max_tokens
            )
        return self._llms[cache_key]
    
    def get_structured_client(self, role: str) -> StructuredLLMClient:
        """Get a structured LLM client for a specific role."""
        if role not in self._structured_clients:
            model_name = self._get_model_for_role(role)
            llm = self.get_chat_model(model_name, role)
            self._structured_clients[role] = StructuredLLMClient(llm)
        return self._structured_clients[role]
    
    def _get_role_config(self, role: str) -> tuple[float, Optional[int]]:
        """Get temperature and max_tokens configuration for a role."""
        if role in ["classifier", "it", "router"]:
            # Low temperature, short responses for precise tasks
            return 0.2, 1000
        elif role == "planner":
            # Slightly higher temperature, more tokens for planning
            return 0.3, 2000
        elif role == "escalation":
            # Higher temperature, more tokens for complex reasoning
            return 0.4, 3000
        else:
            # Default configuration
            return 0.2, 1500
    
    def _get_model_for_role(self, role: str) -> str:
        """Get the appropriate model name for a role."""
        if role == "classifier":
            return settings.classifier_model
        elif role == "planner":
            return settings.planner_model
        elif role == "it":
            return settings.it_model
        elif role == "router":
            return settings.router_model
        elif role == "escalation":
            return settings.escalation_model
        else:
            return settings.classifier_model  # Default fallback


# Global LLM registry instance
llm_registry = LLMRegistry()


def get_llm(role: Literal["classifier", "planner", "it", "router"]) -> BaseChatModel:
    """
    Get an LLM for a specific role with role-specific configuration.
    
    Args:
        role: The role for which to get the LLM
        
    Returns:
        A LangChain chat model configured for the role
        
    Raises:
        ValueError: If the role is not supported
    """
    if role == "classifier":
        return llm_registry.get_chat_model(settings.classifier_model, "classifier")
    elif role == "planner":
        return llm_registry.get_chat_model(settings.planner_model, "planner")
    elif role == "it":
        return llm_registry.get_chat_model(settings.it_model, "it")
    elif role == "router":
        return llm_registry.get_chat_model(settings.router_model, "router")
    else:
        raise ValueError(f"Unsupported role: {role}")


def get_structured_llm_client(role: Literal["classifier", "planner", "it", "router"]) -> StructuredLLMClient:
    """
    Get a structured LLM client for a specific role.
    
    Args:
        role: The role for which to get the structured client
        
    Returns:
        A StructuredLLMClient configured for the role
        
    Raises:
        ValueError: If the role is not supported
    """
    return llm_registry.get_structured_client(role)


def get_escalation_llm() -> BaseChatModel:
    """
    Get the escalation LLM (higher capability model).
    
    Returns:
        A LangChain chat model for escalation scenarios
    """
    return llm_registry.get_chat_model(settings.escalation_model, "escalation")


def switch_provider(provider: Literal["ollama", "vllm", "openrouter"]):
    """
    Switch the LLM provider.
    
    Args:
        provider: The new provider to use
    """
    global llm_registry
    settings.llm_provider = provider
    llm_registry = LLMRegistry()


# Convenience functions for common LLM operations
async def call_llm_with_json_schema(
    role: str,
    prompt: str,
    input_data: Dict[str, Any],
    response_schema: Type[BaseModel],
    system_message: Optional[str] = None
) -> BaseModel:
    """
    Convenience function to call LLM with JSON schema validation.
    
    Args:
        role: The role for the LLM call
        prompt: The prompt template
        input_data: Input data for the prompt
        response_schema: Pydantic model for response validation
        system_message: Optional system message override
        
    Returns:
        Validated response as Pydantic model
    """
    client = get_structured_llm_client(role)
    return await client.call_with_json_schema(prompt, input_data, response_schema, system_message)


async def call_llm_with_function_calling(
    role: str,
    prompt: str,
    input_data: Dict[str, Any],
    tools: List[BaseTool],
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to call LLM with function calling.
    
    Args:
        role: The role for the LLM call
        prompt: The prompt template
        input_data: Input data for the prompt
        tools: List of tools for function calling
        system_message: Optional system message override
        
    Returns:
        Function call results
    """
    client = get_structured_llm_client(role)
    return await client.call_with_function_calling(prompt, input_data, tools, system_message)

