# LLM Registry with Structured Output

The LLM Registry provides a robust, structured approach to LLM interactions with automatic validation, retries, and role-specific configurations.

## Features

### 🔧 **Structured Output with JSON Schema**
- **Automatic Validation**: All LLM responses are validated against Pydantic schemas
- **Type Safety**: Ensures consistent, structured responses across all workflow nodes
- **Error Handling**: Graceful handling of malformed or invalid responses

### 🎯 **Role-Specific Configurations**
- **Classifier/IT/Router**: Low temperature (0.2), short responses (1000 tokens)
- **Planner**: Medium temperature (0.3), longer responses (2000 tokens)  
- **Escalation**: Higher temperature (0.4), extended responses (3000 tokens)

### 🔄 **Automatic Retries with Exponential Backoff**
- **Smart Retry Logic**: Retries on validation errors, JSON parsing failures, and general exceptions
- **Exponential Backoff**: Intelligent delay between retry attempts
- **Configurable Limits**: Adjustable retry counts and delay parameters

### 🛠️ **Function Calling Support**
- **Tool Integration**: Seamless integration with LangChain tools
- **Structured Tool Calls**: Automatic conversion to OpenAI function format
- **Fallback Handling**: Graceful degradation when function calling fails

## Quick Start

### Basic Usage

```python
from src.models.llm_registry import call_llm_with_json_schema
from src.models.response_schemas import ClassifierResponse

# Simple classifier call
response = await call_llm_with_json_schema(
    role="classifier",
    prompt="Analyze this IT support request.",
    input_data={"request": "..."},
    response_schema=ClassifierResponse
)

print(f"Decision: {response.decision}")
print(f"Confidence: {response.confidence}")
```

### Direct Client Usage

```python
from src.models.llm_registry import get_structured_llm_client

# Get client for specific role
client = get_structured_llm_client("planner")

# Call with custom schema
response = await client.call_with_json_schema(
    prompt="Create a plan...",
    input_data={"...": "..."},
    response_schema=YourCustomSchema
)
```

## Configuration

### Environment Variables

```env
# LLM Provider
LLM_PROVIDER=ollama

# Model Names
CLASSIFIER_MODEL=llama3.1:8b
PLANNER_MODEL=mistral:7b
IT_MODEL=llama3.1:8b
ROUTER_MODEL=mistral:7b
ESCALATION_MODEL=mixtral:8x7b

# Temperature Settings
CLASSIFIER_TEMPERATURE=0.2
PLANNER_TEMPERATURE=0.3
IT_TEMPERATURE=0.2
ROUTER_TEMPERATURE=0.2
ESCALATION_TEMPERATURE=0.4

# Token Limits
CLASSIFIER_MAX_TOKENS=1000
PLANNER_MAX_TOKENS=2000
IT_MAX_TOKENS=1000
ROUTER_MAX_TOKENS=1000
ESCALATION_MAX_TOKENS=3000

# Retry Configuration
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY_BASE=1.0
LLM_RETRY_DELAY_MAX=10.0
```

### Role-Specific Settings

| Role | Temperature | Max Tokens | Use Case |
|------|-------------|------------|----------|
| **Classifier** | 0.2 | 1000 | Precise policy classification |
| **Router** | 0.2 | 1000 | Model selection decisions |
| **IT Agent** | 0.2 | 1000 | Action execution planning |
| **Planner** | 0.3 | 2000 | Detailed workflow planning |
| **Escalation** | 0.4 | 3000 | Complex reasoning tasks |

## Response Schemas

### Classifier Response

```python
class ClassifierResponse(BaseModel):
    decision: Literal["ALLOWED", "DENIED", "REQUIRES_APPROVAL"]
    citations: List[Citation]
    confidence: float
    needs_human: bool
    missing_fields: List[str]
    justification_brief: str
```

### Router Response

```python
class RouterResponse(BaseModel):
    target_model: str
    reason: str
    escalation_needed: bool
    model_capabilities: ModelCapabilities
    request_analysis: RequestAnalysis
    quality_metrics: QualityMetrics
```

### Planner Response

```python
class PlannerResponse(BaseModel):
    plan_id: str
    steps: List[PlanStep]
    approval_workflow: ApprovalWorkflow
    risk_assessment: RiskAssessment
    compliance_checklist: List[str]
```

### IT Agent Response

```python
class ITAgentResponse(BaseModel):
    execution_id: str
    executable_actions: List[ExecutableAction]
    user_guide: UserGuide
    completion_package: CompletionPackage
```

## Error Handling

### Automatic Retries

The system automatically retries failed calls with exponential backoff:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ValidationError, json.JSONDecodeError, Exception))
)
```

### Error Types

- **ValidationError**: Response doesn't match expected schema
- **JSONDecodeError**: Malformed JSON response
- **General Exception**: Network, timeout, or other errors

### Fallback Strategies

1. **Retry with same prompt**: Attempt to get valid response
2. **Schema relaxation**: Use more flexible validation if available
3. **Error logging**: Comprehensive error tracking for debugging

## Advanced Usage

### Function Calling

```python
from langchain_core.tools import BaseTool

tools = [EmailTool(), JiraTool(), DirectoryTool()]

response = await call_llm_with_function_calling(
    role="it",
    prompt="Execute this plan using available tools.",
    input_data={"plan": "..."},
    tools=tools
)
```

### Custom Schemas

```python
from pydantic import BaseModel, Field

class CustomResponse(BaseModel):
    action: str = Field(..., description="Action to take")
    priority: int = Field(..., ge=1, le=5, description="Priority level")
    
response = await client.call_with_json_schema(
    prompt="...",
    input_data={"...": "..."},
    response_schema=CustomResponse
)
```

### Batch Processing

```python
import asyncio

async def process_multiple_requests(requests):
    tasks = [
        call_llm_with_json_schema(
            role="classifier",
            prompt="...",
            input_data=req,
            response_schema=ClassifierResponse
        )
        for req in requests
    ]
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return responses
```

## Performance Optimization

### Caching

- **Model Instances**: Cached per provider/model/role combination
- **Structured Clients**: Reused across multiple calls
- **Response Validation**: Efficient schema validation

### Parallel Processing

- **Async Support**: All calls are asynchronous
- **Concurrent Execution**: Multiple LLM calls can run simultaneously
- **Resource Management**: Efficient use of available resources

### Monitoring

- **Call Logging**: Track success/failure rates
- **Performance Metrics**: Response times and token usage
- **Error Analytics**: Identify common failure patterns

## Troubleshooting

### Common Issues

1. **Validation Errors**
   - Check response schema matches expected format
   - Verify LLM output is valid JSON
   - Review prompt for clarity

2. **Retry Failures**
   - Check network connectivity
   - Verify LLM service availability
   - Review rate limiting settings

3. **Performance Issues**
   - Monitor token usage
   - Check model response times
   - Optimize prompt length

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("src.models.llm_registry").setLevel(logging.DEBUG)
```

### Health Checks

```python
from src.models.llm_registry import llm_registry

# Check provider status
provider = llm_registry.get_provider()
print(f"Provider: {provider.__class__.__name__}")

# Test model availability
try:
    model = llm_registry.get_chat_model("test_model", "classifier")
    print("✅ Model available")
except Exception as e:
    print(f"❌ Model error: {e}")
```

## Migration Guide

### From Old LLM Registry

```python
# Old way
from src.models.llm_registry import get_llm
llm = get_llm("classifier")

# New way - structured calls
from src.models.llm_registry import call_llm_with_json_schema
response = await call_llm_with_json_schema(
    role="classifier",
    prompt="...",
    input_data={"...": "..."},
    response_schema=ClassifierResponse
)
```

### Benefits of Migration

- **Type Safety**: Compile-time validation
- **Error Handling**: Automatic retries and fallbacks
- **Consistency**: Standardized response formats
- **Maintainability**: Clear schema definitions
- **Performance**: Optimized configurations per role

## Examples

See `example_structured_calls.py` for comprehensive usage examples covering all workflow nodes and scenarios.
