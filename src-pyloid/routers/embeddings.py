import logging
import os
import shutil
from tempfile import TemporaryDirectory
from typing import Literal
import chromadb
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
import torch
from pathlib import Path
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import SimpleDirectoryReader

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

# Global ChromaDB Client and Collection (initialized on startup)
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION_NAME)

# LlamaIndex Components Setup
embed_model = None
node_parser = None
vector_store = None
pipeline = None

def initialize():
    """
    Initializes the LlamaIndex components and makes them available globally.
    Handles errors gracefully by logging and returning a status.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    global embed_model
    global node_parser
    global vector_store
    global pipeline
    
    logging.info("Starting LlamaIndex component setup...")
    
    try:
        # LlamaIndex Components Setup
        
        # 1. Initialize Embedding Model (Potential model download/name errors)
        embed_model = HuggingFaceEmbedding(
            model_name=EMBED_MODEL_NAME,
            device="cpu" 
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
        
        # 4. Initialize Ingestion Pipeline
        pipeline = IngestionPipeline(
            transformations=[
                node_parser,
                embed_model,
            ],
            vector_store=vector_store,
        )
        logging.info("Successfully initialized all LlamaIndex components.")
        return True
        
    except ImportError as e:
        # Catches errors if required packages (like 'chromadb' or 'transformers') are not installed
        logging.error(f"FATAL ERROR: A required library is missing. Please check your dependencies.")
        logging.error(f"Details: {e}")
        # Optionally, reset globals if any were partially set
        embed_model, node_parser, vector_store, pipeline = None, None, None, None
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