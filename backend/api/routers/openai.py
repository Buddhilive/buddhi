"""
OpenAI-Compatible API Router for model inference.

This router provides OpenAI-compatible endpoints for:
- Chat completions (streaming and non-streaming)
- Text completions
- Model listing

All endpoints require authentication and only work with downloaded models.
"""

import json
import time
from typing import List, Optional, Union, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime

from backend.api.deps import user_dependency
from backend.services.model_manager import model_manager


# OpenAI-compatible Pydantic models
class ChatMessage(BaseModel):
    """Chat message model compatible with OpenAI format."""
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")


class ChatCompletionRequest(BaseModel):
    """Chat completion request model compatible with OpenAI format."""
    model: str = Field(..., description="Name of the model to use")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: Optional[int] = Field(100, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")


class CompletionRequest(BaseModel):
    """Text completion request model compatible with OpenAI format."""
    model: str = Field(..., description="Name of the model to use")
    prompt: str = Field(..., description="Input prompt for text generation")
    max_tokens: Optional[int] = Field(100, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice model compatible with OpenAI format."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class CompletionChoice(BaseModel):
    """Text completion choice model compatible with OpenAI format."""
    index: int
    text: str
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token usage model compatible with OpenAI format."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Chat completion response model compatible with OpenAI format."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Usage] = None


class CompletionResponse(BaseModel):
    """Text completion response model compatible with OpenAI format."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: Optional[Usage] = None


class ModelInfo(BaseModel):
    """Model information model compatible with OpenAI format."""
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: str = "buddhi-ai"


class ModelListResponse(BaseModel):
    """Model list response model compatible with OpenAI format."""
    object: str = "list"
    data: List[ModelInfo]


# Create router with authentication dependency
router = APIRouter(
    prefix="/v1",
    tags=["openai-compatible"],
    dependencies=[Depends(user_dependency)]  # All endpoints require authentication
)


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user: dict = Depends(user_dependency)
):
    """
    Create a chat completion using OpenAI-compatible format.
    
    Supports both streaming and non-streaming responses.
    Only works with downloaded models.
    """
    try:
        # Validate that model is downloaded
        downloaded_models = model_manager.list_downloaded_models()
        model_names = [model["name"] for model in downloaded_models]
        
        if request.model not in model_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{request.model}' is not available. Available models: {model_names}"
            )
        
        # Convert messages to a single prompt
        prompt = _messages_to_prompt(request.messages)
        
        # Generate response ID and timestamp
        response_id = f"chatcmpl-{int(time.time())}{hash(prompt) % 10000}"
        created_timestamp = int(time.time())
        
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                _stream_chat_completion(
                    model_name=request.model,
                    prompt=prompt,
                    max_tokens=request.max_tokens or 100,
                    temperature=request.temperature or 0.7,
                    top_p=request.top_p or 0.9,
                    response_id=response_id,
                    created_timestamp=created_timestamp
                ),
                media_type="text/plain"
            )
        else:
            # Generate non-streaming response
            generated_text = await model_manager.generate(
                model_name=request.model,
                prompt=prompt,
                max_length=request.max_tokens or 100,
                temperature=request.temperature or 0.7,
                top_p=request.top_p or 0.9
            )
            
            # Create response
            response = ChatCompletionResponse(
                id=response_id,
                created=created_timestamp,
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=generated_text),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=len(prompt.split()),  # Rough estimate
                    completion_tokens=len(generated_text.split()),
                    total_tokens=len(prompt.split()) + len(generated_text.split())
                )
            )
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating chat completion: {str(e)}"
        )


@router.post("/completions")
async def create_completion(
    request: CompletionRequest,
    current_user: dict = Depends(user_dependency)
):
    """
    Create a text completion using OpenAI-compatible format.
    
    Supports both streaming and non-streaming responses.
    Only works with downloaded models.
    """
    try:
        # Validate that model is downloaded
        downloaded_models = model_manager.list_downloaded_models()
        model_names = [model["name"] for model in downloaded_models]
        
        if request.model not in model_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{request.model}' is not available. Available models: {model_names}"
            )
        
        # Generate response ID and timestamp
        response_id = f"cmpl-{int(time.time())}{hash(request.prompt) % 10000}"
        created_timestamp = int(time.time())
        
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                _stream_completion(
                    model_name=request.model,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens or 100,
                    temperature=request.temperature or 0.7,
                    top_p=request.top_p or 0.9,
                    response_id=response_id,
                    created_timestamp=created_timestamp
                ),
                media_type="text/plain"
            )
        else:
            # Generate non-streaming response
            generated_text = await model_manager.generate(
                model_name=request.model,
                prompt=request.prompt,
                max_length=request.max_tokens or 100,
                temperature=request.temperature or 0.7,
                top_p=request.top_p or 0.9
            )
            
            # Create response
            response = CompletionResponse(
                id=response_id,
                created=created_timestamp,
                model=request.model,
                choices=[
                    CompletionChoice(
                        index=0,
                        text=generated_text,
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=len(request.prompt.split()),  # Rough estimate
                    completion_tokens=len(generated_text.split()),
                    total_tokens=len(request.prompt.split()) + len(generated_text.split())
                )
            )
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating completion: {str(e)}"
        )


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    current_user: dict = Depends(user_dependency)
):
    """
    List available models in OpenAI-compatible format.
    
    Returns only downloaded models that are available for inference.
    """
    try:
        # Get downloaded models
        downloaded_models = model_manager.list_downloaded_models()
        
        # Convert to OpenAI format
        models = [
            ModelInfo(
                id=model["name"],
                created=int(datetime.fromisoformat(model["download_date"]).timestamp()) 
                       if model["download_date"] else None,
                owned_by="buddhi-ai"
            )
            for model in downloaded_models
        ]
        
        return ModelListResponse(data=models)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing models: {str(e)}"
        )


# Helper functions
def _messages_to_prompt(messages: List[ChatMessage]) -> str:
    """Convert chat messages to a single prompt string."""
    prompt_parts = []
    
    for message in messages:
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"User: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    # Add assistant prompt at the end
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)


async def _stream_chat_completion(
    model_name: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    response_id: str,
    created_timestamp: int
) -> AsyncGenerator[str, None]:
    """Stream chat completion response in OpenAI format."""
    try:
        # Stream the generation
        async for chunk in model_manager.generate_stream(
            model_name=model_name,
            prompt=prompt,
            max_length=max_tokens,
            temperature=temperature,
            top_p=top_p
        ):
            # Format as OpenAI streaming response
            delta = {
                "role": "assistant",
                "content": chunk
            }
            
            stream_response = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created_timestamp,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": delta,
                        "finish_reason": None
                    }
                ]
            }
            
            yield f"data: {json.dumps(stream_response)}\n\n"
        
        # Send final message
        final_response = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created_timestamp,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        
        yield f"data: {json.dumps(final_response)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_response = {
            "error": {
                "message": f"Error during streaming: {str(e)}",
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_response)}\n\n"


async def _stream_completion(
    model_name: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    response_id: str,
    created_timestamp: int
) -> AsyncGenerator[str, None]:
    """Stream text completion response in OpenAI format."""
    try:
        # Stream the generation
        async for chunk in model_manager.generate_stream(
            model_name=model_name,
            prompt=prompt,
            max_length=max_tokens,
            temperature=temperature,
            top_p=top_p
        ):
            # Format as OpenAI streaming response
            stream_response = {
                "id": response_id,
                "object": "text_completion",
                "created": created_timestamp,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "text": chunk,
                        "finish_reason": None
                    }
                ]
            }
            
            yield f"data: {json.dumps(stream_response)}\n\n"
        
        # Send final message
        final_response = {
            "id": response_id,
            "object": "text_completion",
            "created": created_timestamp,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "text": "",
                    "finish_reason": "stop"
                }
            ]
        }
        
        yield f"data: {json.dumps(final_response)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_response = {
            "error": {
                "message": f"Error during streaming: {str(e)}",
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_response)}\n\n"
