from contextlib import asynccontextmanager
import os
import signal
import sys
from pyloid_adapter.fastapi_adapter import FastAPIAdapter, PyloidContext
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import embeddings
# from routers import completions

# Lifespan hook
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that runs on application startup and shutdown.
    It's a context manager (yield) structure.
    """
    try:
        # Preload the models
        embeddings.initialize()
        # completions.load_model()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load models: {e}")
        
    yield
    print("[Buddhi AI] Shutting down...", flush=True)
    kill_process()

app = FastAPI(
    title="Buddhi AI API server",
    version="0.1.0",
    lifespan=lifespan
)

BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
# --- Construct the absolute path to the static folder ---
STATIC_FILES_DIR = os.path.join(BUNDLE_DIR, 'static')
app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")

# Add CORS middleware directly to ensure it's applied properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def start(host: str, port: int):
	import uvicorn

	uvicorn.run(app, host=host, port=port)


def setup_cors():
	app.add_middleware(
		CORSMiddleware,
		allow_origins=['*'],
		allow_credentials=True,
		allow_methods=['*'],
		allow_headers=['*'],
	)


adapter = FastAPIAdapter(start, setup_cors)


@app.get('/greet')
async def greet(name: str):
	return f'Hello, {name}!'


@app.get('/create_window')
async def create_window(request: Request):
	ctx: PyloidContext = adapter.get_context(request)
	win = ctx.pyloid.create_window(title='Google Window')
	win.load_url('https://www.google.com')
	win.show_and_focus()

# Include Routers
# app.include_router(completions.COMPLETIONS_ROUTER)
app.include_router(embeddings.EMBEDDING_ROUTER)

# Programmatically force shutdown the server.
def kill_process():
    os.kill(os.getpid(), signal.SIGINT)
