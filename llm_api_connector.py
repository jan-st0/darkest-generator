import httpx
from pydantic import BaseModel, Field
from typing import Any

class Prompt(BaseModel):
  model: str
  input: str
  system_prompt: str | None = None
  integrations: list[str | Any] = Field(default_factory=list)
  stream: bool | None = None
  temperature: float | None = None
  top_p: float | None = None
  top_k: float | None = None
  min_p: float | None = None
  repeat_penalty: float | None = None
  max_output_tokens: int | None = None
  reasoning: str | None = None
  context_length: int | None = None
  store: bool | None = None
  previous_response_id: str | None = None


class ModelOutputMessage(BaseModel):
  type: str
  content: str


class ToolProviderInfo(BaseModel):
  type: str
  plugin_id: str | None = None
  server_label: str | None = None


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
  arguments: Any = None
  provider_info: ToolProviderInfo


class InvalidToolCall(BaseModel):
  type: str
  reason: str
  metadata: InvalidToolCallMetadata


class ModelOutputStats(BaseModel):
  input_tokens: int
  total_output_tokens: int
  reasoning_output_tokens: int
  tokens_per_second: float
  time_to_first_token_seconds: float
  model_load_time_seconds: float | None = None


class ModelResponse(BaseModel):
  model_instance_id: str | None = None
  output: list[ModelOutputMessage | OutputToolCall | InvalidToolCall | ModelReasoning] = Field(default_factory=list)
  stats: ModelOutputStats
  response_id: str | None = None


def send_model_message(client: httpx.Client, prompt: Prompt) -> ModelResponse:
  response = client.post(
      "/api/v1/chat", json=prompt.model_dump(exclude_none=True)
  )
  response.raise_for_status()
  return ModelResponse.model_validate(response.json())

# test

with httpx.Client(base_url="http://localhost:1234", timeout=600.0) as client:
    model_name = "qwen/qwen3-14b"
    input_text = "Explain all strategies of constraint handling in evolutionary algorithms facing discrete combinatoral optimization promblems."
    promptPayload = Prompt(model=model_name, input=input_text, reasoning="on")
    result = send_model_message(client, promptPayload)
    print(f"{result.stats}")
    out = result.output
    with open('model_reasoning.md', 'w') as f:
        f.write('\n'.join([output.content for output in out if output.type == 'reasoning']))
    
    with open('model_out.md', 'w') as f:
        f.write('\n'.join([output.content for output in out if output.type == 'message']))