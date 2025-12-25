from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any

# Import your AI Brain
from app.ai.graph import app_graph
from langchain_core.messages import HumanMessage

router = APIRouter()

# Simple In-Memory Database for Chat History
# (In production, use Redis)
MEMORY_STORE = {}


class ChatRequest(BaseModel):
    message: str
    role: str = "guest"


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_id = "default_user"  # Simplified for now

    # 1. Retrieve History
    history = MEMORY_STORE.get(user_id, [])

    # 2. Add User Message
    history.append(HumanMessage(content=req.message))

    # 3. Process with LangGraph
    # We pass the role to the state so the prompt knows who is talking
    state = {"messages": history, "user_role": req.role}
    result = app_graph.invoke(state)

    # 4. Extract AI Response
    bot_msg = result["messages"][-1]

    # 5. Update History
    # LangGraph returns the full updated list, so we save that
    MEMORY_STORE[user_id] = result["messages"]

    return {"response": bot_msg.content}


@router.post("/reset")
async def reset_endpoint(req: ChatRequest):
    user_id = "default_user"
    if user_id in MEMORY_STORE:
        MEMORY_STORE[user_id] = []
    return {"status": "Memory cleared"}