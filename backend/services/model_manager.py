"""
Model Manager Service for handling Hugging Face model operations.

This service provides functionality to:
- Search Hugging Face models
- Download and cache models locally
- Track download status and progress
- Load models for inference
- Generate responses (streaming and non-streaming)
- Persist model metadata to database
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from huggingface_hub import list_models, snapshot_download
from huggingface_hub.utils import HfHubHTTPError
from sqlalchemy.orm import Session

from backend.models.base import Model
from backend.api.database import SessionLocal


class ModelManager:
    """Manages Hugging Face model operations including search, download, and inference."""
    
    def __init__(self, cache_dir: str = "./models_cache"):
        """Initialize the ModelManager with a specified cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory storage for loaded models and download status
        self.loaded_models: Dict[str, Any] = {}
        self.download_status: Dict[str, Dict[str, Any]] = {}
        
    def get_db(self) -> Session:
        """Get database session."""
        db = SessionLocal()
        try:
            return db
        finally:
            pass  # Don't close here as it's used in context managers
    
    async def search_models(
        self, 
        query: str, 
        limit: int = 20,
        model_type: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Hugging Face models by query string.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            model_type: Filter by model type (e.g., 'text-generation')
            language: Filter by language (e.g., 'en')
            
        Returns:
            List of model dictionaries with metadata
        """
        try:
            # Search models using HuggingFace Hub
            search_kwargs = {
                "search": query,
                "limit": limit,
                "sort": "downloads",
                "direction": -1  # Descending order (most downloads first)
            }
            
            # Add task filter if specified
            if model_type:
                search_kwargs["task"] = model_type
            
            models = list_models(**search_kwargs)
            
            # Convert ModelInfo objects to dictionaries
            results = []
            for model in models:
                model_dict = {
                    "id": model.id,
                    "author": getattr(model, 'author', None),
                    "downloads": getattr(model, 'downloads', 0),
                    "likes": getattr(model, 'likes', 0),
                    "created_at": getattr(model, 'created_at', None),
                    "last_modified": getattr(model, 'last_modified', None),
                    "tags": getattr(model, 'tags', []),
                    "pipeline_tag": getattr(model, 'pipeline_tag', None),
                    "library_name": getattr(model, 'library_name', None),
                    "model_type": getattr(model, 'pipeline_tag', 'unknown'),
                }
                
                # Filter by language if specified
                if language and language not in str(model_dict.get('tags', [])).lower():
                    continue
                    
                results.append(model_dict)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error searching models: {str(e)}")
    
    async def download_model(self, model_name: str) -> Dict[str, Any]:
        """
        Download a model from Hugging Face and cache it locally.
        
        Args:
            model_name: Name of the model to download (e.g., 'gpt2')
            
        Returns:
            Dictionary with download status and metadata
        """
        try:
            # Initialize download status
            self.download_status[model_name] = {
                "status": "starting",
                "progress": 0,
                "message": "Initializing download...",
                "started_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Check if model already exists in database
            with SessionLocal() as db:
                existing_model = db.query(Model).filter(Model.name == model_name).first()
                if existing_model and existing_model.status == "downloaded":
                    self.download_status[model_name] = {
                        "status": "completed",
                        "progress": 100,
                        "message": "Model already downloaded",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                    return self.download_status[model_name]
            
            # Update status to downloading
            self.download_status[model_name].update({
                "status": "downloading",
                "progress": 10,
                "message": "Downloading model files..."
            })
            
            # Create model-specific cache directory
            model_cache_path = self.cache_dir / model_name.replace("/", "_")
            model_cache_path.mkdir(exist_ok=True)
            
            # Download model using snapshot_download for better control
            try:
                local_path = snapshot_download(
                    repo_id=model_name,
                    cache_dir=str(model_cache_path),
                    local_files_only=False
                )
                
                # Update progress
                self.download_status[model_name].update({
                    "progress": 80,
                    "message": "Download completed, saving metadata..."
                })
                
                # Get model metadata
                model_info = await self._get_model_info(model_name)
                
                # Calculate model size
                model_size = self._calculate_model_size(local_path)
                
                # Save model info to database
                with SessionLocal() as db:
                    # Check if model exists, update or create
                    db_model = db.query(Model).filter(Model.name == model_name).first()
                    if db_model:
                        # Update existing model
                        db_model.local_path = local_path
                        db_model.status = "downloaded"
                        db_model.download_date = datetime.now(timezone.utc)
                        db_model.size_bytes = model_size
                        db_model.updated_at = datetime.now(timezone.utc)
                    else:
                        # Create new model record
                        db_model = Model(
                            name=model_name,
                            local_path=local_path,
                            status="downloaded",
                            size_bytes=model_size,
                            model_type=model_info.get("pipeline_tag", "unknown"),
                            description=model_info.get("description", ""),
                            author=model_info.get("author", ""),
                            license=model_info.get("license", ""),
                            language=model_info.get("language", ""),
                            tags=json.dumps(model_info.get("tags", [])),
                            downloads=model_info.get("downloads", 0),
                            likes=model_info.get("likes", 0)
                        )
                        db.add(db_model)
                    
                    db.commit()
                    db.refresh(db_model)
                
                # Update final status
                self.download_status[model_name].update({
                    "status": "completed",
                    "progress": 100,
                    "message": "Model downloaded successfully",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "local_path": local_path,
                    "size_bytes": model_size
                })
                
                return self.download_status[model_name]
                
            except HfHubHTTPError as e:
                error_msg = f"Failed to download model: {str(e)}"
                self.download_status[model_name].update({
                    "status": "failed",
                    "message": error_msg,
                    "error": str(e),
                    "failed_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Update database status
                with SessionLocal() as db:
                    db_model = db.query(Model).filter(Model.name == model_name).first()
                    if db_model:
                        db_model.status = "failed"
                        db_model.updated_at = datetime.now(timezone.utc)
                        db.commit()
                
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Error downloading model {model_name}: {str(e)}"
            self.download_status[model_name] = {
                "status": "failed",
                "message": error_msg,
                "error": str(e),
                "failed_at": datetime.now(timezone.utc).isoformat()
            }
            raise Exception(error_msg)
    
    def get_download_status(self, model_name: str) -> Dict[str, Any]:
        """
        Get download status for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with current download status
        """
        return self.download_status.get(model_name, {"status": "not_started"})
    
    def list_downloaded_models(self) -> List[Dict[str, Any]]:
        """
        List all downloaded models from the database.
        
        Returns:
            List of downloaded model dictionaries
        """
        with SessionLocal() as db:
            models = db.query(Model).filter(Model.status == "downloaded").all()
            
            return [
                {
                    "id": model.id,
                    "name": model.name,
                    "local_path": model.local_path,
                    "status": model.status,
                    "download_date": model.download_date.isoformat() if model.download_date else None,
                    "size_bytes": model.size_bytes,
                    "model_type": model.model_type,
                    "description": model.description,
                    "author": model.author,
                    "license": model.license,
                    "language": model.language,
                    "tags": json.loads(model.tags) if model.tags else [],
                    "downloads": model.downloads,
                    "likes": model.likes,
                    "created_at": model.created_at.isoformat() if model.created_at else None,
                    "updated_at": model.updated_at.isoformat() if model.updated_at else None
                }
                for model in models
            ]
    
    async def load_model(self, model_name: str) -> Any:
        """
        Load a model for inference. Models are cached in memory after first load.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded model object
        """
        # Check if model is already loaded
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        # Check if model is downloaded
        with SessionLocal() as db:
            db_model = db.query(Model).filter(
                Model.name == model_name,
                Model.status == "downloaded"
            ).first()
            
            if not db_model:
                raise Exception(f"Model {model_name} not found or not downloaded")
        
        try:
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(db_model.local_path)
            model = AutoModelForCausalLM.from_pretrained(
                db_model.local_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Create pipeline for easier inference
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Cache the loaded model
            self.loaded_models[model_name] = {
                "model": model,
                "tokenizer": tokenizer,
                "pipeline": pipe,
                "loaded_at": datetime.now(timezone.utc)
            }
            
            return self.loaded_models[model_name]
            
        except Exception as e:
            raise Exception(f"Error loading model {model_name}: {str(e)}")
    
    async def generate(
        self,
        model_name: str,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        Generate text using the specified model.
        
        Args:
            model_name: Name of the model to use
            prompt: Input prompt text
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text string
        """
        try:
            # Load model if not already loaded
            model_obj = await self.load_model(model_name)
            pipe = model_obj["pipeline"]
            
            # Generate text
            result = pipe(
                prompt,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=pipe.tokenizer.eos_token_id,
                **kwargs
            )
            
            # Extract generated text
            generated_text = result[0]["generated_text"]
            
            # Remove the original prompt from the result
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            raise Exception(f"Error generating text with model {model_name}: {str(e)}")
    
    async def generate_stream(
        self,
        model_name: str,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using streaming for real-time response.
        
        Args:
            model_name: Name of the model to use
            prompt: Input prompt text
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            **kwargs: Additional generation parameters
            
        Yields:
            Text chunks as they are generated
        """
        try:
            # Load model if not already loaded
            model_obj = await self.load_model(model_name)
            model = model_obj["model"]
            tokenizer = model_obj["tokenizer"]
            
            # Encode the prompt
            inputs = tokenizer.encode(prompt, return_tensors="pt")
            
            # Set up generation parameters
            generation_config = {
                "max_length": len(inputs[0]) + max_length,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": True,
                "pad_token_id": tokenizer.eos_token_id,
                **kwargs
            }
            
            # Generate tokens one by one
            with torch.no_grad():
                for _ in range(max_length):
                    outputs = model.generate(
                        inputs,
                        max_length=inputs.shape[1] + 1,
                        **{k: v for k, v in generation_config.items() if k != "max_length"}
                    )
                    
                    # Get the new token
                    new_token_id = outputs[0, -1:]
                    new_token = tokenizer.decode(new_token_id, skip_special_tokens=True)
                    
                    # Check for end of sequence
                    if new_token_id.item() == tokenizer.eos_token_id:
                        break
                    
                    # Yield the new token
                    yield new_token
                    
                    # Update inputs for next iteration
                    inputs = outputs
                    
                    # Small delay for streaming effect
                    await asyncio.sleep(0.05)
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def _get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get model information from Hugging Face Hub.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model metadata
        """
        try:
            # Search for the specific model
            models = list_models(search=model_name, limit=1)
            for model in models:
                if model.id == model_name:
                    return {
                        "id": model.id,
                        "author": getattr(model, 'author', ''),
                        "downloads": getattr(model, 'downloads', 0),
                        "likes": getattr(model, 'likes', 0),
                        "tags": getattr(model, 'tags', []),
                        "pipeline_tag": getattr(model, 'pipeline_tag', 'unknown'),
                        "library_name": getattr(model, 'library_name', ''),
                        "description": getattr(model, 'description', ''),
                        "license": getattr(model, 'license', ''),
                        "language": getattr(model, 'language', '')
                    }
            
            # If not found in search, return minimal info
            return {
                "id": model_name,
                "author": "",
                "downloads": 0,
                "likes": 0,
                "tags": [],
                "pipeline_tag": "unknown",
                "library_name": "",
                "description": "",
                "license": "",
                "language": ""
            }
            
        except Exception:
            # Return minimal info on error
            return {
                "id": model_name,
                "author": "",
                "downloads": 0,
                "likes": 0,
                "tags": [],
                "pipeline_tag": "unknown",
                "library_name": "",
                "description": "",
                "license": "",
                "language": ""
            }
    
    def _calculate_model_size(self, model_path: str) -> int:
        """
        Calculate the total size of a model directory in bytes.
        
        Args:
            model_path: Path to the model directory
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(model_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size


# Global model manager instance
model_manager = ModelManager()
