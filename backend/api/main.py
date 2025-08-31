from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import auth, model_management, openai

app = FastAPI(
    title="Buddhi AI",
    description="AI Model Orchestration Service with OpenAI-compatible API",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def health_check():
    return {"message": "Welcome to Buddhi AI!"}

# Include routers
app.include_router(auth.router)
app.include_router(model_management.router)
app.include_router(openai.router)
