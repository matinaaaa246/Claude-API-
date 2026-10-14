import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import time

from browser_manager import PlaywrightManager, ResourceExhaustedError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("claude-api")

manager = PlaywrightManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.startup()
    yield
    await manager.shutdown()

app = FastAPI(title="Claude API Unofficial", lifespan=lifespan)

class PromptRequest(BaseModel):
    prompt: str

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "claude-3-5-sonnet"
    messages: List[ChatMessage]
    stream: Optional[bool] = False

@app.get("/")
@app.get("/health")
async def health_check():
    active_sessions = sum(1 for s in manager.sessions if not s.is_exhausted)
    return {
        "status": "healthy",
        "total_sessions": len(manager.sessions),
        "active_sessions": active_sessions
    }

@app.post("/ask")
async def ask_endpoint(req: PromptRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    try:
        reply = await manager.process_prompt(req.prompt)
        return {"response": reply}
    except ResourceExhaustedError:
        raise HTTPException(status_code=429, detail="All Claude accounts have reached message limits.")
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
    
    # Extract last user message or build a conversation context
    last_msg = req.messages[-1]
    prompt_text = ""
    if isinstance(last_msg.content, str):
        prompt_text = last_msg.content
    elif isinstance(last_msg.content, list):
        for item in last_msg.content:
            if isinstance(item, dict) and item.get("type") == "text":
                prompt_text += item.get("text", "")
    
    if not prompt_text:
        raise HTTPException(status_code=400, detail="No prompt text found in last message")

    try:
        reply = await manager.process_prompt(prompt_text)
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt_text.split()),
                "completion_tokens": len(reply.split()),
                "total_tokens": len(prompt_text.split()) + len(reply.split())
            }
        }
    except ResourceExhaustedError:
        raise HTTPException(status_code=429, detail="All Claude accounts have reached message limits.")
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
