import operator
import traceback
from typing import TypedDict, Annotated, List

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings

# --- IMPORT ALL TOOLS ---
from app.ai.tools.availability import check_availability_tool
from app.ai.tools.booking import book_room_tool
from app.ai.tools.guest_info import get_guest_info_tool
from app.ai.tools.stats import hotel_stats_tool

# ============================================================
# 1. DEFINE TOOLKITS
# ============================================================
guest_tools = [check_availability_tool, book_room_tool]
manager_tools = [hotel_stats_tool, get_guest_info_tool, check_availability_tool]

# Master list for the ToolNode
all_tools = [check_availability_tool, book_room_tool, get_guest_info_tool, hotel_stats_tool]

# ============================================================
# 2. SETUP LLM
# ============================================================
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    api_key=settings.GROQ_API_KEY
)


# ============================================================
# 3. DEFINE STATE
# ============================================================
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_role: str


# ============================================================
# 4. THE BRAIN (CHATBOT NODE)
# ============================================================
def chatbot_node(state: AgentState):
    """
    Decides which Persona (Guest vs Manager) to run.
    """
    try:
        messages = state.get("messages", [])
        role = state.get("user_role", "guest")

        # --- A. SELECT PERSONA ---
        if role == "manager":
            tools_subset = manager_tools
            system_prompt = (
                "You are the **Grand Hotel Executive Assistant**.\n"
                "**PROTOCOL:**\n"
                "1. If asked 'Status' or 'Revenue', run `hotel_stats_tool`.\n"
                "2. If asked about a guest, run `get_guest_info_tool`.\n"
                "3. Summarize the data clearly.\n"
                "**STRICT:** Do not book rooms. You are an analyst."
            )
        else:
            # 🛎️ GUEST PERSONA
            tools_subset = guest_tools
            system_prompt = (
                "You are the **Grand Hotel Concierge**. Warm, professional, and precise.\n\n"
                "**GOAL:** Help the user book a room. Collect: Dates, Room, Guest Count, Name, Email.\n\n"
                "**PROTOCOL:**\n"
                "1. **Inquiry:** Confirm features (if asked).\n"
                "2. **Dates First:** IF you do not have check-in/out dates, ASK for them. **DO NOT call `check_availability_tool` without valid dates.**\n"
                "3. **Check:** Once you have dates, use `check_availability_tool`.\n"
                "4. **Offer:** Show Rooms. Filter irrelevant ones.\n"
                "5. **Details:** Ask for Guest Count (Adults/Children).\n"
                "6. **Finalize:** Ask Name/Email -> `book_room_tool`.\n\n"

                "**🚨 CRITICAL RULES:**\n"
                "- **NO GUESSING:** Never call a tool with placeholders like 'YYYY-MM-DD'. If parameters are missing, ASK the user.\n"
                "- **MULTIPLE BOOKINGS:** A single guest (same email) CAN book multiple rooms. Do not block this.\n"
                "- **STOPPING RULE:** Once `book_room_tool` returns 'Success', stop. Say: 'Booking confirmed! Check your email.'\n"
                "- **VOICE:** Never say 'I will use the tool'. Just say 'I am checking availability now'."
                "- **CONTEXT:** If the user gives all info at once, book immediately."
            )

        # --- B. BIND TOOLS ---
        llm_with_specific_tools = llm.bind_tools(tools_subset)

        # --- C. CONTEXT MANAGEMENT (Fixed Window) ---
        sys_msg = SystemMessage(content=system_prompt)

        # Filter history (Keep last 50 messages)
        history = [m for m in messages if not isinstance(m, SystemMessage)]
        if len(history) > 50:
            history = history[-50:]

        full_conversation = [sys_msg] + history

        # --- D. INVOKE ---
        response = llm_with_specific_tools.invoke(full_conversation)
        return {"messages": [response]}

    except Exception as e:
        # 🚨 DEBUG: Print the actual error to the terminal so we can fix it
        print(f"\n❌ CRITICAL ERROR IN CHATBOT NODE: {e}\n")
        traceback.print_exc()

        return {
            "messages": [AIMessage(content="I'm experiencing high traffic. Please try again.")],
        }


# ============================================================
# 5. BUILD THE GRAPH
# ============================================================
workflow = StateGraph(AgentState)

workflow.add_node("agent", chatbot_node)
workflow.add_node("tools", ToolNode(all_tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

app_graph = workflow.compile()