import os
from typing import TypedDict
from fastapi import APIRouter, Body
from transformers import pipeline
import torch

router = APIRouter(prefix="/v1", tags=["llm"])
model_path = "static/models/gemma-3-270m-it"

class T_Query(TypedDict):
    prompt: str

@router.post("/completions")
async def completion(payload: T_Query = Body(...)):
    pipe = pipeline("text-generation", model=model_path, device="cpu", dtype=torch.bfloat16)

    messages = [
        [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."},]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": payload["prompt"]},]
            },
        ],
    ]

    output = pipe(messages, max_new_tokens=50)
    return output

