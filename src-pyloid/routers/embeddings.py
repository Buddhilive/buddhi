import logging
import os
import shutil
from tempfile import TemporaryDirectory
from typing import List, Literal, Optional
import chromadb
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
import torch
from pathlib import Path
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import SimpleDirectoryReader, StorageContext, Settings, VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configuration
logging.basicConfig(level=logging.INFO)
EMBEDDING_ROUTER = APIRouter(prefix="/v1/embeddings", tags=["Embeddings"])
CURRENT_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Construct the absolute path to the model
BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Sentence Transformer model name for EmbeddingGemma
EMBED_MODEL_NAME = os.path.join(BUNDLE_DIR, 'static', 'models', 'embeddinggemma-300m')
# Directory for ChromaDB persistence (it will be created if it doesn't exist)
CHROMA_PERSIST_DIR = os.path.join(Path.home(), ".buddhi-ai","kb")
# Name of the ChromaDB collection
CHROMA_COLLECTION_NAME = "pdf_rag_collection"
TOP_K = 3

# Global ChromaDB Client and Collection (initialized on startup)
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION_NAME)

# Model Configuration
LLM_MODEL_NAME = os.path.join(BUNDLE_DIR, 'static', 'models', 'gemma-3-270m-it') 
LLM_SYSTEM_PROMPT = """You are an expert AI assistant providing answers based ONLY on the private documents provided in the context.
If the answer is not in the documents, state clearly that you cannot answer from the provided information."""

# LlamaIndex Components Setup
embed_model = None
node_parser = None
vector_store = None
pipeline = None
retriever = None
query_engine = None
llm = None
vector_index = None
chat_engine = None

def initialize():
    """
    Initializes the LlamaIndex components and makes them available globally.
    Handles errors gracefully by logging and returning a status.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    global embed_model, node_parser, vector_store, pipeline, retriever, query_engine
    global llm, vector_index, chat_engine
    
    logging.info("Starting LlamaIndex component setup...")
    
    try:
        # LlamaIndex Components Setup
        
        # 1. Initialize Embedding Model (Potential model download/name errors)
        embed_model = HuggingFaceEmbedding(
            model_name=EMBED_MODEL_NAME,
            device=CURRENT_DEVICE 
        )
        logging.info(f"Initialized embedding model: {EMBED_MODEL_NAME}")
        
        # 2. Initialize Node Parser (Less likely to fail unless arguments are wrong)
        node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=20,
        )
        logging.info("Initialized node parser.")
        
        # 3. Initialize Vector Store (Potential connection/collection errors)
        # Note: 'chroma_collection' must be available in the global scope or passed in
        # If 'chroma_collection' is invalid or not defined, this will fail.
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        logging.info("Initialized Chroma vector store.")
        
        # 4. Initialize LLM
        # Note: You might need to adjust parameters like context_window for your specific model/hardware.
        # This setup attempts to use the model on the available device.
        logging.info(f"Initializing HuggingFace LLM: {LLM_MODEL_NAME} on device: {CURRENT_DEVICE}")
        
        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)

        llm = HuggingFaceLLM(
            context_window=8192,  # Set based on the LLM's capability
            max_new_tokens=2048,
            generate_kwargs={"temperature": 0.1, "do_sample": True},
            system_prompt=LLM_SYSTEM_PROMPT,
            tokenizer=tokenizer,
            model=AutoModelForCausalLM.from_pretrained(
                LLM_MODEL_NAME, 
                device_map=str(CURRENT_DEVICE), # Use device_map for better loading
                dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32 
            ),
            device_map=str(CURRENT_DEVICE),
        )
        Settings.llm = llm # Set the global LLM setting
        logging.info(f"Initialized LLM: {LLM_MODEL_NAME}")
        
        # 5. Setup Index, Retriever, and Query/Chat Engines 
        pipeline = IngestionPipeline(
            transformations=[node_parser, embed_model],
            vector_store=vector_store,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create/Load VectorIndex
        vector_index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model,
            storage_context=storage_context
        )

        # Retriever setup for /query_pdf/ (Context retrieval, no synthesis)
        retriever = vector_index.as_retriever(similarity_top_k=TOP_K)
        query_engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=None)

        # Chat Engine setup for /chat/completions/ (Retrieval-Augmented Generation)
        # We use CondenseQuestionChatEngine for stateful chat that still uses the retriever (RAG)
        chat_engine = CondenseQuestionChatEngine.from_defaults(
            retriever=retriever,
            llm=llm,
            verbose=True, # Set to False in production
            query_engine=query_engine,
        )
        
        logging.info("Successfully initialized all LlamaIndex components (including LLM and Chat Engine).")
        return True
        
    except ImportError as e:
        # Catches errors if required packages (like 'chromadb' or 'transformers') are not installed
        logging.error(f"FATAL ERROR: A required library is missing. Please check your dependencies.")
        logging.error(f"Details: {e}")
        # Optionally, reset globals if any were partially set
        embed_model, node_parser, vector_store, pipeline = None, None, None, None
        llm, vector_index, chat_engine = None, None, None
        return False
        
    except Exception as e:
        # Catch any other general exceptions (e.g., FileNotFoundError, connection issues, invalid arguments)
        logging.error("An unexpected error occurred during LlamaIndex component setup.")
        logging.error(f"Details: {e}")
        # Optionally, print the full traceback for debugging if needed
        # import traceback; traceback.print_exc()
        
        # Reset global variables to None to clearly indicate failure
        embed_model, node_parser, vector_store, pipeline = None, None, None, None
        return False


# Pydantic Models for Type Safety and API Documentation
class IndexResponse(BaseModel):
    """Pydantic model for the successful indexing response."""
    status: Literal["success"]
    filename: str
    document_id: str | None
    message: str
    chunks_created: int
    vector_store: str
    collection: str
    embedding_model: str

class ResetResponse(BaseModel):
    """Pydantic model for the collection reset response."""
    status: Literal["success"]
    message: str

class QueryRequest(BaseModel):
    """Pydantic model for the query request body."""
    query: str = Field(..., description="The natural language query to search the documents.")

class MatchingChunk(BaseModel):
    """Pydantic model for a single retrieved chunk."""
    text: str = Field(..., description="The relevant text content from the document.")
    similarity_score: float = Field(..., description="The similarity score of the chunk to the query.")
    source_filename: str | None = Field(None, description="The original filename this chunk came from.")

class QueryResponse(BaseModel):
    """Pydantic model for the retrieval query response."""
    query: str
    retrieval_model: str
    top_k: int
    matches: List[MatchingChunk] = Field(..., description="A list of the most relevant document chunks.")

class Message(BaseModel):
    """OpenAI standard message object."""
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    """OpenAI standard completion API request body."""
    model: str = Field(LLM_MODEL_NAME, description="The LLM model name. Defaults to Gemma.")
    messages: List[Message]
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 2048
    # Not all fields are strictly required, but included for standard compliance

class ChatCompletionChoice(BaseModel):
    """OpenAI standard choice object."""
    index: int
    message: Message
    finish_reason: Literal["stop", "length", "content_filter"]

class Usage(BaseModel):
    """OpenAI standard usage object."""
    prompt_tokens: int = 0 # LlamaIndex doesn't easily provide token counts here
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    """OpenAI standard completion API response body."""
    id: str = "chatcmpl-1234567890"
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(..., description="Timestamp of the response.")
    model: str = LLM_MODEL_NAME
    choices: List[ChatCompletionChoice]
    usage: Usage

# FastAPI Endpoints
@EMBEDDING_ROUTER.post("/upload_and_index_pdf/", response_model=IndexResponse)
async def upload_and_index_pdf(file: UploadFile = File(...)):
    """
    Uploads a PDF, chunks it using LlamaIndex, generates embeddings 
    with EmbeddingGemma, and stores them in a persistent ChromaDB.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are supported."
        )

    # Use a temporary directory to save the uploaded file
    with TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / file.filename
        
        # Save the uploaded file locally
        try:
            with temp_file_path.open("wb") as buffer:
                while content := await file.read(1024 * 1024):  # 1MB chunks
                    buffer.write(content)
        except Exception as e:
            # Re-raise as an HTTPException to be handled by FastAPI
            raise HTTPException(
                status_code=500, detail=f"Error saving file locally: {e}"
            )

        # LlamaIndex: Load document
        try:
            loader = SimpleDirectoryReader(input_files=[temp_file_path])
            documents = loader.load_data()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"LlamaIndex document loading error: {e}"
            )
        
        # LlamaIndex Ingestion Pipeline: Chunk, Embed, and Store
        try:
            nodes = pipeline.run(documents=documents)
            num_chunks = len(nodes)
            doc_id = documents[0].doc_id if documents else None
            
            # The response now conforms to the Pydantic IndexResponse model
            return IndexResponse(
                status="success",
                filename=file.filename,
                document_id=doc_id,
                message=f"Successfully processed and indexed {file.filename}.",
                chunks_created=num_chunks,
                vector_store="ChromaDB Persistent Client",
                collection=CHROMA_COLLECTION_NAME,
                embedding_model=EMBED_MODEL_NAME,
            )
        
        except Exception as e:
            # Clean up temporary files (context manager handles this, but good practice)
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(
                status_code=500, 
                detail=f"LlamaIndex ingestion pipeline error (chunking/embedding/storage): {e}"
            )

# Delete collection
@EMBEDDING_ROUTER.delete("/reset_chroma_collection/", response_model=ResetResponse)
async def reset_chroma_collection():
    """Deletes and recreates the ChromaDB collection."""
    try:
        global chroma_collection, vector_store, pipeline

        # 1. Delete and Recreate Collection
        chroma_client.delete_collection(name=CHROMA_COLLECTION_NAME)
        chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION_NAME)
        
        # 2. Re-initialize LlamaIndex components with the new collection
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        pipeline = IngestionPipeline(
            transformations=[node_parser, embed_model],
            vector_store=vector_store,
        )
        
        # The response now conforms to the Pydantic ResetResponse model
        return ResetResponse(
            status="success", 
            message=f"ChromaDB collection '{CHROMA_COLLECTION_NAME}' reset successfully. The persistent directory '{CHROMA_PERSIST_DIR}' remains intact."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error resetting ChromaDB collection: {e}"
        )
    
# Query Vector Database
@EMBEDDING_ROUTER.post("/query_pdf/", response_model=QueryResponse)
async def query_pdf(request: QueryRequest):
    """
    Sends a query to the ChromaDB vector store and retrieves the top-K matching 
    document chunks using the EmbeddingGemma model.
    """
    try:
        # Use the LlamaIndex query engine to handle embedding and retrieval
        response = query_engine.query(request.query)
        
        # Process the source nodes from the response into the Pydantic format
        matching_chunks = []
        for node_with_score in response.source_nodes:
            # Get the similarity score provided by LlamaIndex
            score = node_with_score.score
            # Get the text content of the node (chunk)
            text = node_with_score.text
            # Extract metadata (assuming the PDF loader adds 'file_name' metadata)
            filename = node_with_score.metadata.get('file_name', 'Unknown')
            
            matching_chunks.append(
                MatchingChunk(
                    text=text,
                    similarity_score=score,
                    source_filename=filename
                )
            )

        # Return the final Pydantic response
        return QueryResponse(
            query=request.query,
            retrieval_model=EMBED_MODEL_NAME,
            top_k=TOP_K,
            matches=matching_chunks
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during PDF retrieval: {e}"
        )

# Chat Completion Endpoint
@EMBEDDING_ROUTER.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-standard chat completion endpoint. Uses LlamaIndex's CondenseQuestionChatEngine 
    with Gemma to answer user queries using context from the vectorized PDF documents.
    """
    if not chat_engine:
        raise HTTPException(status_code=503, detail="Chat engine is not initialized. Please ensure initialization succeeded.")
        
    # Extract the latest user message (assuming standard chat flow)
    user_message = next((m.content for m in reversed(request.messages) if m.role == "user"), None)

    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found in the request messages.")
    
    # Send the user query to the LlamaIndex chat engine
    try:
        # LlamaIndex's chat engine handles history internally
        response = chat_engine.chat(user_message)
        
        # Note: LlamaIndex response object doesn't provide easy access to token usage
        # or a standard 'finish_reason', so we'll use sensible defaults.
        
        current_timestamp = int(os.times()[4])
        
        # Construct the response in the OpenAI standard format
        return ChatCompletionResponse(
            id="chatcmpl-custom-rag-1",
            object="chat.completion",
            created=current_timestamp,
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(role="assistant", content=response.response),
                    finish_reason="stop" # Assuming a natural stop
                )
            ],
            usage=Usage(
                prompt_tokens=0, # Default to 0 due to difficulty in accurate tracking
                completion_tokens=0,
                total_tokens=0
            )
        )

    except Exception as e:
        logging.error(f"Error during chat completion: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing chat request: {e}"
        )
