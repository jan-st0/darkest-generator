import httpx
from pydantic import BaseModel, Field
from typing import Any

class Prompt(BaseModel):
    model: str
    input: str
    system_prompt: str | None
    integrations: list[str | Any] | None
    stream: bool | None
    temperature: float | None
    top_p: float | None
    top_k: float | None
    min_p: float | None
    repeat_penalty: float | None
    max_output_tokens: int | None
    reasoning: str | None
    context_length: int | None
    store: bool | None
    previous_response_id: str | None

class ModelOutputMessage(BaseModel):
    type: str
    content: str

class ToolProviderInfo(BaseModel):
    type: str
    plugin_id: str | None
    server_label: str | None

class OutputToolCall(BaseModel):
    type: str
    tool: str
    arguments: str
    output: str
    provider_info: ToolProviderInfo

class ModelReasoning(BaseModel):
    type: str
    content: str

class InvalidToolCallMetadata(BaseModel):
    type: str
    tool_name: str
    arguments: Any
    provider_info: ToolProviderInfo

class InvalidToolCall(BaseModel):
    type: str
    reason: str
    metadata: InvalidToolCallMetadata

class ModelOutput(BaseModel):
    message: ModelOutputMessage
    tool_call: OutputToolCall
    reasoning: ModelReasoning
    invalid_tool_call: InvalidToolCall

class ModelOutputStats(BaseModel):
    input_tokens: int
    total_output_tokens: int
    reasoning_output_tokens: int
    tokens_per_second: float
    time_to_first_token_seconds: float
    model_load_time_seconds: float | None

class ModelResponse(BaseModel):
    model_instance_id: str | None
    output: list[ModelOutput]
    stats: ModelOutputStats
    response_id: str | None
    
def send_model_message(client: httpx.Client, prompt: Prompt) -> ModelResponse:
    response = client.post("/api/v1/chat", json=prompt.model_dump_json())
    response.raise_for_status()
    return ModelResponse.model_validate(response.json())

# test

with httpx.Client(base_url="http://localhost:1234", timeout=60.0) as client:
    model_name = "qwen/qwen3-14b"
    input = "Explain all strategies of constraint handling in evolutionary algorithms facing discrete combinatoral optimization promblems."
    promptPayload = Prompt(model=model_name, input=input, reasoning="on")
    result = send_model_message(client, promptPayload)
    print(f'{result=}')
