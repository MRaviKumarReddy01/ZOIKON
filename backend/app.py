from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

from pathlib import Path

app = FastAPI()

# mount frontend safely
BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ correct frontend path

# serve frontend
frontend_path = BASE_DIR / "frontend"

print("Frontend path:", frontend_path)   # debug

app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

class Message(BaseModel):
    message: str

def load_knowledge():
    with open("data/knowledge.json") as f:
        return json.load(f)

knowledge = load_knowledge()

@app.post("/chat")
def chat(msg: Message):
    user_msg = msg.message.lower()

    for k, v in knowledge.items():
        if k in user_msg:
            return {"response": v}

    return {"response": "I don't know yet."}