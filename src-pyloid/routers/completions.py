import logging
import os
import time
from typing import Generator, List, Optional, Literal
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from transformers import pipeline, TextStreamer
import queue
import torch
import uuid
from anyio.to_thread import run_sync

# Configurations
logging.basicConfig(level=logging.INFO)
COMPLETIONS_ROUTER = APIRouter(prefix="/v1", tags=["Chat"])
# Construct the absolute path to the model
BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM_MODEL_NAME = os.path.join(BUNDLE_DIR, 'static', 'models', 'gemma-3-270m-it')
CURRENT_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LLM_SYSTEM_PROMPT = """You are an expert AI assistant providing answers based ONLY on the private documents provided in the context.
If the answer is not in the documents, state clearly that you cannot answer from the provided information."""

BUDDHI_AI_PIPELINE = None

# Load the HuggingFace pipeline once when the application starts
def load_model():
    try:
        global BUDDHI_AI_PIPELINE
        # Check if the model path exists locally
        if not os.path.exists(LLM_MODEL_NAME):
            raise FileNotFoundError(f"Model directory not found: {LLM_MODEL_NAME}")
        
        logging.info("\tLoading Chat model...")
        
        # Use torch.bfloat16 only if the device and model support it
        BUDDHI_AI_PIPELINE = pipeline(
            "text-generation",
            model=LLM_MODEL_NAME,
            device=CURRENT_DEVICE, # Use "cuda" if a GPU is available
            dtype=torch.bfloat16, # Use torch.float32 if bfloat16 is not supported
        )
        logging.info("\tBuddhi AI Pipeline loaded successfully")
    except Exception as e:
        # If model loading fails, the API should not start or should return 500
        logging.error(f"Error loading model: {e}")
        BUDDHI_AI_PIPELINE = None 


# Pydantic Models for OpenAI Chat Completions Standard

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
    It expects either a list of messages or a single prompt string.
    """
    model: str = Field(
        LLM_MODEL_NAME, description="The LLM model name. Defaults to Gemma."
    )
    messages: Optional[List[ChatMessage]] = Field(None, description="The conversation history.")
    prompt: Optional[str] = Field(None, description="The input prompt for completion.")
    
    # Include other common OpenAI parameters (optional and set to defaults)
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=50, ge=1)
    stream: Optional[bool] = False

    @model_validator(mode='after')
    def validate_messages_or_prompt(self):
        if self.messages is None and self.prompt is None:
            raise ValueError("Either 'messages' or 'prompt' must be provided.")
        if self.messages is not None and self.prompt is not None:
            # If both are provided, prioritize messages as per requirements
            self.prompt = None
        if self.messages is not None and len(self.messages) == 0:
            raise ValueError("'messages' must not be empty if provided.")
        return self

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

class ChatCompletionChunkDelta(BaseModel):
    """The delta object containing only the content change."""
    role: Optional[Literal['assistant']] = None
    content: Optional[str] = None
    
class ChatCompletionChunkChoice(BaseModel):
    """Represents a single generated completion chunk in a stream."""
    index: int
    delta: ChatCompletionChunkDelta
    # finish_reason is only present in the final chunk
    finish_reason: Optional[Literal['stop', 'length', 'tool_calls', 'content_filter', 'function_call', 'null']] = None

class ChatCompletionChunk(BaseModel):
    """The main response object for a single chunk in the stream."""
    id: str = Field(..., description="A unique identifier for the chat completion.")
    object: Literal['chat.completion.chunk'] = 'chat.completion.chunk' # NOTE THE 'chunk' object type
    created: int = Field(..., description="The Unix timestamp (in seconds) of when the chat completion was created.")
    model: str = Field(..., description="The model used for the chat completion.")
    choices: List[ChatCompletionChunkChoice]

# Standardized Chat Completion Endpoint

@COMPLETIONS_ROUTER.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    payload: CreateChatCompletionRequest
):
    """
    OpenAI-standard chat completion endpoint using the HuggingFace pipeline.
    
    Maps the standard request structure (messages) to the pipeline and 
    then formats the output to match the standard OpenAI response.
    Supports both messages array and prompt string parameters.
    """
    if BUDDHI_AI_PIPELINE is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Service unavailable."
        )

    # 1. Adapt Input for Hugging Face Pipeline
    hf_messages = []
    
    if payload.messages is not None:
        # Handle messages array (chat completions format)
        hf_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in payload.messages
            if msg.content is not None # Filter out messages with None content for text-only model
        ]
    elif payload.prompt is not None:
        # Handle prompt string (completions format)
        # Treat the prompt as a user message
        hf_messages = [
            {"role": "user", "content": payload.prompt}
        ]
    
    if not hf_messages:
        raise HTTPException(
            status_code=400,
            detail="Request must contain either 'messages' with content or a 'prompt' string."
        )
    
    # Check for streaming request ------------------------------------------
    if payload.stream:
        # Return a StreamingResponse using a generator function
        generator_stream = await run_sync(
            stream_generator_wrapper,
            BUDDHI_AI_PIPELINE,
            hf_messages,
            payload.max_tokens,
            payload.model
        )
        
        # Return a StreamingResponse using the synchronous generator object
        return StreamingResponse(
            generator_stream, # Pass the synchronous generator here
            media_type="text/event-stream"
        )

    # 2. Run Generation
    
    # The 'BUDDHI_AI_PIPELINE' function is synchronous, which blocks the event loop.
    # For a production application, you should run this in a separate thread
    # using `await run_in_threadpool()` or similar.
    # For this implementation, we proceed synchronously for simplicity.
    
    start_time = time.time()
    
    # Note: max_new_tokens is derived from the OpenAI-style max_tokens parameter
    output = BUDDHI_AI_PIPELINE(
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
    
    # Estimate Token Usage (Simplified)
    # NOTE: Accurate token counting requires the model's tokenizer.
    # We use a rough, character-based estimate for this sample.
    chars_per_token = 4
    input_text = " ".join([m['content'] for m in hf_messages])
    
    prompt_tokens = len(input_text) // chars_per_token
    completion_tokens = len(generated_text) // chars_per_token
    total_tokens = prompt_tokens + completion_tokens

    # Build the Final Response
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

# NEW FUNCTION FOR STREAMING

class CustomTextStreamer(TextStreamer):
    """
    A custom streamer that writes tokens to a queue instead of stdout, 
    allowing them to be yielded by the FastAPI generator.
    """
    def __init__(self, tokenizer, skip_prompt=True, **kwargs):
        super().__init__(tokenizer, skip_prompt, **kwargs)
        self.queue = queue.Queue()
        self.stop_signal = object()

    def on_finalized_text(self, text: str, stream_end: bool = False):
        """Called when a full chunk of text (including special tokens or a full sentence) is ready."""
        # This sends the token chunk to the generator
        self.queue.put(text)
        if stream_end:
            self.queue.put(self.stop_signal)

    def __iter__(self):
        """The generator that yields tokens."""
        return self

    def __next__(self):
        """Blocking call to wait for the next token chunk."""
        item = self.queue.get(timeout=60) # Set a reasonable timeout
        if item is self.stop_signal:
            raise StopIteration()
        return item


def stream_generator_wrapper(
    pipeline_instance, 
    hf_messages: List[dict], 
    max_tokens: Optional[int], 
    model_name: str
) -> Generator[str, None, None]:
    """
    Wraps model generation with CustomTextStreamer for token-by-token output.
    """
    
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:20]}"
    created_time = int(time.time())
    
    # 1. Yield the initial chunk with the role
    chunk = ChatCompletionChunk(
        id=completion_id,
        object='chat.completion.chunk',
        created=created_time,
        model=model_name,
        choices=[ChatCompletionChunkChoice(
            index=0,
            delta=ChatCompletionChunkDelta(role='assistant'),
        )]
    )
    yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
    
    # 2. Setup and Run Streaming Generation
    
    # Extract tokenizer and model from the pipeline
    tokenizer = pipeline_instance.tokenizer
    model = pipeline_instance.model
    
    # Tokenize the input messages
    # NOTE: The apply_chat_template handles the formatting and returns input IDs
    input_ids = tokenizer.apply_chat_template(
        hf_messages, 
        tokenize=True, 
        add_generation_prompt=True, 
        return_tensors="pt"
    ).to(model.device) # Move to the correct device (CPU/CUDA)
    
    # Initialize the custom streamer
    streamer = CustomTextStreamer(tokenizer, skip_prompt=True)
    
    # Define generation arguments
    generation_kwargs = {
        "max_new_tokens": max_tokens if max_tokens else 50,
        "do_sample": True if pipeline_instance.framework == "pt" else False, # or base on payload.temperature
        "temperature": 1.0, # or use payload.temperature
        "streamer": streamer, # KEY CHANGE: Pass the streamer here
        "input_ids": input_ids,
        "attention_mask": None, # Should be handled by input_ids if needed
    }
    
    # We must run model.generate in a separate thread so the streamer.queue.get() 
    # doesn't block the caller thread (which is already a worker thread from anyio).
    # Since we are already in a worker thread via run_sync, we can call it directly,
    # but we need to run it concurrently to allow the generator to yield.
    
    import threading

    def generate_task():
        """The target function for the thread to run model generation."""
        try:
            # Call the model's generate method directly
            model.generate(**generation_kwargs)
        except Exception as e:
            logging.error(f"Generation thread error: {e}")
            # Ensure the queue is stopped on error
            streamer.queue.put(streamer.stop_signal)

    # Start the generation in a background thread
    thread = threading.Thread(target=generate_task)
    thread.start()
    
    # 3. Yield Chunks from the Streamer
    
    # Iterate over the custom streamer, which yields the chunks
    for new_text in streamer:
        if new_text:
            chunk = ChatCompletionChunk(
                id=completion_id,
                object='chat.completion.chunk',
                created=created_time,
                model=model_name,
                choices=[ChatCompletionChunkChoice(
                    index=0,
                    delta=ChatCompletionChunkDelta(content=new_text)
                )]
            )
            # Send the chunk formatted as SSE
            yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
            
    # Wait for the generation thread to finish before concluding the stream
    thread.join()

    # 4. Yield the final chunk and DONE marker
    final_chunk = ChatCompletionChunk(
        id=completion_id,
        object='chat.completion.chunk',
        created=created_time,
        model=model_name,
        choices=[ChatCompletionChunkChoice(
            index=0,
            delta=ChatCompletionChunkDelta(), 
            finish_reason='stop' 
        )]
    )
    yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"
    
    yield "data: [DONE]\n\n"
