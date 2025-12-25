import os
import sys
import operator
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from app.ai.tools.guest_info import get_guest_info_tool

from langchain_groq import ChatGroq
import operator
from typing import TypedDict, Annotated, List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from app.core.config import settings
from app.ai.tools.availability import check_availability_tool
from app.ai.tools.booking import book_room_tool
from app.core.config import settings

# Define the tools list
tools = [check_availability_tool, book_room_tool]
tools = [check_availability_tool, book_room_tool, get_guest_info_tool]

# ============================================================
# 2. SETUP LLM
# ============================================================
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    api_key=settings.GROQ_API_KEY
)
llm_with_tools = llm.bind_tools(tools)


# ============================================================
# 3. DEFINE STATE
# ============================================================
class AgentState(TypedDict):
    # 'operator.add' appends new messages to the history list
    messages: Annotated[List[BaseMessage], operator.add]
    user_role: str


# ============================================================
# 4. THE BRAIN (CHATBOT NODE)
# ============================================================
def chatbot_node(state: AgentState):
    """
    Bulletproof chatbot node with error handling, history management,
    and strict anti-hallucination prompts.
    """

    # --- A. SAFE STATE EXTRACTION ---
    try:
        messages = state.get("messages", [])
        role = state.get("user_role", "guest")

        if not isinstance(messages, list):
            messages = []
        if role not in ["guest", "manager"]:
            role = "guest"

    except Exception as e:
        return {
            "messages": [AIMessage(content="System Error: State extraction failed.")],
        }

    # --- B. BUILD SYSTEM PROMPT ---
    if role == "guest":
        system_prompt = (
            "You are the **Grand Hotel Concierge**. Warm, professional, and precise.\n\n"
            "**STRICT BOOKING PROTOCOL (FOLLOW ORDER):**\n"
            "1. **Inquiry:** If user asks to book, FIRST ask: 'What dates would you like to stay?'\n"
            "2. **Check:** Once you have dates, use `check_availability_tool`. DO NOT guess availability.\n"
            "3. **Offer:** Show the available rooms. **IMPORTANT:** If the user asked for specific features (e.g., 'city view', 'balcony'), ONLY list the rooms that match those features. Do not show irrelevant rooms.\n"
            "4. **Book:** ONLY when user selects a specific room, say exactly:\n"
            "   'Great choice! To confirm your booking, please provide your **Full Name** and **Email Address**.'\n\n"
            "**RULES:**\n"
            "- Capture the name/email from their reply and use the 'book_room_tool'.\n"
            "- If availability tool returns nothing, apologize and suggest new dates."
        )
    elif role == "manager":
        system_prompt = (
            "You are the **Grand Hotel Executive Assistant**. You provide high-level administrative "
            "support and business intelligence to the Hotel Manager.\n\n"
            "**PROHIBITED ACTIONS:**\n"
            "- DO NOT attempt to book rooms.\n"
            
            "**REQUIRED ACTIONS:**\n"
            "- Provide summaries of bookings, revenue insights, and room occupancy stats.\n"
            "- Use the available tools to query the database for current records.\n"
            "- Be concise, professional, and focus on data trends."
            "- If the manager asks about a guest, use the `get_guest_info_tool`.\n"
            "- You must ask for the guest's email if they haven't provided it.\n\n"
        )

    sys_msg = SystemMessage(content=system_prompt)

    # --- C. CONTEXT MANAGEMENT (SLIDING WINDOW) ---
    try:
        # Filter out old SystemMessages to prevent duplicates stacking up
        history = [m for m in messages if not isinstance(m, SystemMessage)]

        # Keep only last 20 messages to prevent hitting token limits (Latency Optimization)
        if len(history) > 20:
            history = history[-20:]

        # Validated message list
        full_conversation = [sys_msg] + history

    except Exception:
        full_conversation = [sys_msg] + messages[-5:]  # Emergency fallback

    # --- D. INVOKE LLM ---
    try:
        response = llm_with_tools.invoke(full_conversation)
        return {"messages": [response]}

    except Exception as e:
        return {
            "messages": [AIMessage(content="I'm experiencing high traffic. Please try again.")],
        }


# ============================================================
# 5. SAFETY WRAPPER
# ============================================================
def safe_chatbot_node(state: AgentState):
    """
    Catches ANY crash in the main logic to keep the server alive.
    """
    try:
        return chatbot_node(state)
    except Exception as e:
        return {
            "messages": [AIMessage(content="Critical System Error. Please reset the chat.")],
        }


# ============================================================
# 6. BUILD THE GRAPH
# ============================================================
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", safe_chatbot_node)  # Use the safe wrapper!
workflow.add_node("tools", ToolNode(tools))

# Define Flow
workflow.set_entry_point("agent")

# Logic: If Agent calls a tool -> go to Tools. Otherwise -> END.
workflow.add_conditional_edges("agent", tools_condition)

# Logic: After Tools run -> go back to Agent to interpret results.
workflow.add_edge("tools", "agent")

# Compile
app_graph = workflow.compile()