from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Allow CORS for development, as Tauri's dev server runs on a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set this to your Tauri dev URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/greet")
async def greet_user(name: str):
    return {"message": f"Namo Buddhaya!, {name} from FastAPI!"}

if __name__ == "__main__":
    # The host should be 127.0.0.1 for local communication
    uvicorn.run(app, host="127.0.0.1", port=5000)
