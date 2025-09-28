import os
import time
from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
from transformers import pipeline
import torch
import uuid

COMPLETIONS_ROUTER = APIRouter(prefix="/v1", tags=["llm"])
model_path = "static/models/gemma-3-270m-it"
current_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

pipe = None

# Load the HuggingFace pipeline once when the application starts
def load_model():
    try:
        global pipe
        # Use torch.bfloat16 only if the device and model support it
        pipe = pipeline(
            "text-generation",
            model=model_path,
            device=current_device, # Use "cuda" if a GPU is available
            dtype=torch.bfloat16 # Use torch.float32 if bfloat16 is not supported
        )
        print(f"HuggingFace Pipeline loaded successfully with model: {model_path}")
    except Exception as e:
        # If model loading fails, the API should not start or should return 500
        print(f"Error loading model: {e}")
        pipe = None 


# --- Pydantic Models for OpenAI Chat Completions Standard ---

# Request Models (Input)

ChatRole = Literal['system', 'user', 'assistant', 'tool'] # Valid roles

class ChatMessage(BaseModel):
    """A single message object in the OpenAI Chat Completions request."""
    role: ChatRole
    # For simplicity, we only allow str content for this basic implementation.
    # The full spec supports array content for multimodal, but the HF pipeline
    # here is assumed to handle only text.
    content: Optional[str] = None
    
    # Other optional fields (like name, tool_calls) are omitted for brevity

class CreateChatCompletionRequest(BaseModel):
    """
    Request body for the /v1/chat/completions endpoint.
    It expects a list of messages and a model ID.
    """
    model: str = Field(..., description="The model to use for completion.")
    messages: List[ChatMessage] = Field(..., min_length=1, description="The conversation history.")
    
    # Include other common OpenAI parameters (optional and set to defaults)
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=50, ge=1)
    # The 'stream' parameter is omitted as this simple example does not implement streaming.


# Response Models (Output)

class Usage(BaseModel):
    """Model for token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponseMessage(BaseModel):
    """The message object from the assistant."""
    role: Literal['assistant']
    content: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    """Represents a single generated completion."""
    index: int
    message: ChatCompletionResponseMessage
    # finish_reason must be one of the specified enums
    finish_reason: Literal['stop', 'length', 'tool_calls', 'content_filter', 'function_call', 'null']

class ChatCompletionResponse(BaseModel):
    """
    The main response object for a successful chat completion.
    Reference: Example response in openapi.yaml.
    """
    id: str = Field(..., description="A unique identifier for the chat completion.")
    object: Literal['chat.completion'] = 'chat.completion'
    created: int = Field(..., description="The Unix timestamp (in seconds) of when the chat completion was created.")
    model: str = Field(..., description="The model used for the chat completion.")
    choices: List[ChatCompletionChoice]
    usage: Usage


# --- Standardized Chat Completion Endpoint ---

@COMPLETIONS_ROUTER.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    payload: CreateChatCompletionRequest
):
    """
    OpenAI-standard chat completion endpoint using the HuggingFace pipeline.
    
    Maps the standard request structure (messages) to the pipeline and 
    then formats the output to match the standard OpenAI response.
    """
    if pipe is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Service unavailable."
        )

    # 1. Adapt Input for Hugging Face Pipeline
    
    # The HF pipeline expects a specific list of message dictionaries.
    # We must convert the Pydantic model's list of ChatMessage to the
    # format expected by the tokenizer/pipeline (e.g., {"role": str, "content": str}).
    hf_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in payload.messages
        if msg.content is not None # Filter out messages with None content for text-only model
    ]
    
    if not hf_messages:
        raise HTTPException(
            status_code=400,
            detail="Request must contain at least one message with content."
        )

    # 2. Run Generation
    
    # The 'pipe' function is synchronous, which blocks the event loop.
    # For a production application, you should run this in a separate thread
    # using `await run_in_threadpool()` or similar.
    # For this implementation, we proceed synchronously for simplicity.
    
    start_time = time.time()
    
    # Note: max_new_tokens is derived from the OpenAI-style max_tokens parameter
    output = pipe(
        hf_messages,
        max_new_tokens=payload.max_tokens if payload.max_tokens else 50,
        return_full_text=False # Get only the new generated text
    )
    
    generation_time = time.time() - start_time
    
    # 3. Process and Format Output to OpenAI Standard
    
    # The pipeline output is typically a list of dicts, e.g., [{'generated_text': '...'}]
    
    # Check if we got any valid response
    if not output or 'generated_text' not in output[0]:
        raise HTTPException(
            status_code=500,
            detail="Model generated an empty or unexpected response."
        )

    generated_text = output[0]['generated_text']
    
    # --- Estimate Token Usage (Simplified) ---
    # NOTE: Accurate token counting requires the model's tokenizer.
    # We use a rough, character-based estimate for this sample.
    chars_per_token = 4
    input_text = " ".join([m['content'] for m in hf_messages])
    
    prompt_tokens = len(input_text) // chars_per_token
    completion_tokens = len(generated_text) // chars_per_token
    total_tokens = prompt_tokens + completion_tokens

    # --- Build the Final Response ---
    
    response_message = ChatCompletionResponseMessage(
        role='assistant',
        content=generated_text.strip()
    )
    
    choice = ChatCompletionChoice(
        index=0,
        message=response_message,
        # Set finish_reason based on standard behavior. 'length' if max_tokens hit, 'stop' otherwise.
        finish_reason='length' if len(generated_text) >= (payload.max_tokens or 50) * chars_per_token else 'stop' 
    )

    usage_data = Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )
    
    # Final Pydantic validation of the response structure
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:20]}",
        object='chat.completion',
        created=int(time.time()),
        model=payload.model,
        choices=[choice],
        usage=usage_data
    )
