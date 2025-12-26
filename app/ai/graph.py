import operator
import traceback
from typing import TypedDict, Annotated, List

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, BaseMessage, ToolMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings

# --- IMPORT TOOLS ---
from app.ai.tools.availability import check_availability_tool
from app.ai.tools.booking import book_room_tool
from app.ai.tools.guest_info import get_guest_info_tool
from app.ai.tools.stats import hotel_stats_tool

# ============================================================
# 1. DEFINE TOOLKITS
# ============================================================
guest_tools = [check_availability_tool, book_room_tool]
manager_tools = [hotel_stats_tool, get_guest_info_tool, check_availability_tool]
all_tools = [check_availability_tool, book_room_tool, get_guest_info_tool, hotel_stats_tool]

# ============================================================
# 2. SETUP LLM
# ============================================================
llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
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
    try:
        messages = state.get("messages", [])
        role = state.get("user_role", "guest")

        if role == "manager":
            tools_subset = manager_tools
            system_prompt = (
                "You are the **Grand Hotel Executive Assistant**.\n"
                "**PROTOCOL:**\n"
                "1. If asked 'Status' or 'Revenue', run `hotel_stats_tool`.\n"
                "2. If asked about a guest, run `get_guest_info_tool`.\n"
                "3. If asked about room availability, run `check_availability_tool`.\n"
                "4. If asked about list of rooms, run `check_availability_tool`.\n"
                "5. Whenever asked about above queries, tell them in proper tabular format.\n"
                "6. Summarize data clearly.\n"
                "**STRICT:** Do not book rooms. You are an analyst.\n"

            )
        else:
            # 🛎️ GUEST PERSONA - REINFORCED TRIGGER
            tools_subset = guest_tools
            system_prompt = (
                "You are the **Grand Hotel Concierge**. Warm, professional, and precise.\n\n"
                "**GOAL:** Help the user book a room. Follow these steps strictly:\n"
                "1. **Inquiry:** Confirm features and ask for check-in/out dates.\n"
                "2. **Check:** Use `check_availability_tool` ONLY when you have valid dates.\n"
                "3. **Offer:** Present available rooms clearly.\n"
                "4. **Pre-Confirmation:** Once a user picks a room, summarize: Room, Dates, and Guest count.\n"
                "   Ask: 'Shall I proceed with opening the reservation form for you?'\n"
                "5. **Trigger:** ONLY if the user gives a positive confirmation (e.g., 'Yes', 'Proceed'), "
                "reply with the exact phrase: 'I am opening the reservation form now. <SHOW_BOOKING_FORM>'\n\n"
                "**🚨 CRITICAL RULES:**\n"
                "- **NO HIDDEN FORMS:** Do not use <SHOW_BOOKING_FORM> until the user says YES to your summary.\n"
                "- **SYSTEM ALERTS:** If you see a 'SYSTEM ALERT' confirming a booking, stop the sales process. "
                "Welcome them to the hotel and ask if they need anything else.\n"
                "- **VOICE:** Be professional. Never say 'I will use a tool'."
            )

        llm_with_specific_tools = llm.bind_tools(tools_subset)
        sys_msg = SystemMessage(content=system_prompt)

        # Keep last 30 messages for memory stability
        history = [m for m in messages if not isinstance(m, SystemMessage)]
        if len(history) > 30:
            history = history[-30:]

        full_conversation = [sys_msg] + history
        response = llm_with_specific_tools.invoke(full_conversation)
        return {"messages": [response]}

    except Exception as e:
        traceback.print_exc()
        return {
            "messages": [AIMessage(content="I'm having trouble connecting to the concierge desk. Please try again.")],
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