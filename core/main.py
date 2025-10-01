from contextlib import asynccontextmanager
import os
import signal
import sys
import asyncio
import threading
import logging
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server
from fastapi.staticfiles import StaticFiles

from routers import embeddings
from routers import completions

PORT_API = 8008

server_instance = None  # Global reference to the Uvicorn server instance

# Lifespan hook
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that runs on application startup and shutdown.
    It's a context manager (yield) structure.
    """
    try:
        # Preload the models
        embeddings.load_model()
        completions.load_model()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load models: {e}")
        
    yield
    print("[sidecar] Shutting down...", flush=True)
    kill_process()


# Programmatically force shutdown this sidecar.
def kill_process():
    os.kill(os.getpid(), signal.SIGINT)  # This force closes this script.

app = FastAPI(
    title="Buddhi AI API server",
    version="0.1.0",
    lifespan=lifespan
)

# --- Determine the base path for bundled files ---
# This is the directory where PyInstaller unpacked the files at runtime.
if getattr(sys, 'frozen', False):
    # Running inside a PyInstaller bundle
    BUNDLE_DIR = sys._MEIPASS
else:
    # Running as a regular Python script (for development)
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Construct the absolute path to the static folder ---
STATIC_FILES_DIR = os.path.join(BUNDLE_DIR, 'static')

# --- Initialize StaticFiles with the correct path ---
# Ensure 'app' is your FastAPI instance
app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")

# Configure CORS settings
origins = [
    "*",  # to whitelist any url, REMOVE THIS FOR PRODUCTION!!!
    # "http://localhost:3000", # for dev
    # "https://your-web-ui.com", # for prod
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tell client we are ready to accept requests.
# This is a mock func, modify to your needs.
@app.get("/health")
def connect_to_api_server():
    """
    Check API Server health.
    """
    print("[server] Connecting to server...", flush=True)
    host = f"http://localhost:{PORT_API}"
    return {
        "message": f"Connected to api server on port {PORT_API}. Refer to '{host}/docs' for api docs.",
        "data": {
            "port": PORT_API,
            "pid": os.getpid(),
            "host": host,
        },
    }

# Include Routers
app.include_router(completions.COMPLETIONS_ROUTER)
app.include_router(embeddings.EMBEDDING_ROUTER)

# Programmatically startup the api server
def start_api_server(**kwargs):
    global server_instance
    port = kwargs.get("port", PORT_API)
    try:
        if server_instance is None:
            print("[sidecar] Starting API server...", flush=True)
            # Configure Uvicorn to use custom logging setup
            config = Config(
                app, 
                host="0.0.0.0", 
                port=port, 
                log_level="info",
                # Disable Uvicorn's default access log to reduce noise
                access_log=False,
                # Use default logger to have more control over output
                use_colors=False
            )
            server_instance = Server(config)
            # Start the ASGI server
            asyncio.run(server_instance.serve())
        else:
            print(
                "[sidecar] Failed to start new server. Server instance already running.",
                flush=True,
            )
    except Exception as e:
        print(f"[sidecar] Error, failed to start API server {e}", flush=True)


# Handle the stdin event loop. This can be used like a CLI.
def stdin_loop():
    print("[sidecar] Waiting for commands...", flush=True)
    while True:
        # Read input from stdin.
        user_input = sys.stdin.readline().strip()

        # Check if the input matches one of the available functions
        match user_input:
            case "sidecar shutdown":
                print("[sidecar] Received 'sidecar shutdown' command.", flush=True)
                kill_process()
            case _:
                print(
                    f"[sidecar] Invalid command [{user_input}]. Try again.", flush=True
                )


# Start the input loop in a separate thread
def start_input_thread():
    try:
        input_thread = threading.Thread(target=stdin_loop)
        input_thread.daemon = True  # so it exits when the main program exits
        input_thread.start()
    except:
        print("[sidecar] Failed to start input handler.", flush=True)


if __name__ == "__main__":
    # You can spawn sub-processes here before the main process.
    # new_command = ["python", "-m", "some_script", "--arg", "argValue"]
    # subprocess.Popen(new_command)

    # Listen for stdin from parent process
    start_input_thread()

    # Starts API server, blocks further code from execution.
    start_api_server()