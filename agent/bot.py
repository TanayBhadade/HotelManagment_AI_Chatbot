import os
import sys
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime

# Import all tools (Including the new ones for Manager)
from agent.tools import (
    check_availability, book_room, get_booking_details,
    generate_daily_report, get_todays_bookings,
    get_room_info_tool, get_todays_checkins, get_upcoming_bookings
)

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    sys.exit(" Error: GROQ_API_KEY missing.")

llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)


# --- 1. TOOLS DEFINITION ---
@tool
def check_availability_tool(start_date: str, end_date: str):
    """Checks availability. Dates: YYYY-MM-DD."""
    return check_availability(start_date, end_date)


@tool
def book_room_tool(room_number: str, name: str, email: str, start_date: str, end_date: str, adults: str, children: str):
    """Books a room. Requires Name, Email, Dates, Room No, and Counts."""
    return book_room(room_number, name, email, start_date, end_date, adults, children)


@tool
def get_booking_details_tool(email: str):
    """Finds booking details by email."""
    return get_booking_details(email)


@tool
def daily_report_tool(dummy_query: str = "report"):
    """Get revenue and stats. Input ignored."""
    return generate_daily_report()


@tool
def todays_bookings_tool(dummy_query: str = "today"):
    """Get list of CURRENTLY staying guests (Occupancy). Input ignored."""
    return get_todays_bookings()


@tool
def get_todays_checkins_tool(dummy_query: str = "checkins"):
    """Get a list of guests ARRIVING today (Check-ins)."""
    return get_todays_checkins()


@tool
def get_upcoming_bookings_tool(dummy_query: str = "future"):
    """Get the full schedule of booked rooms and their dates."""
    return get_upcoming_bookings()


# List of tools provided to the agent
tools = [
    check_availability_tool,
    book_room_tool,
    get_booking_details_tool,
    daily_report_tool,
    todays_bookings_tool,
    get_room_info_tool,
    get_todays_checkins_tool,
    get_upcoming_bookings_tool
]

# --- 2. PROMPT DEFINITION (STRICT LOGIC) ---
# This must be defined BEFORE the 'agent = ...' line below.
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are the **Grand Hotel AI Assistant**, a warm, professional, and helpful assistant. Today is {today}.\n"
        "Current User Role: **{user_role}**\n\n"

        "🎯 **YOUR GOAL:**\n"
        "Adapt behavior strictly based on `user_role`.\n\n"

        "👤 **IF USER IS A GUEST ({user_role} = 'guest'):**\n"
        "   **🌊 CONVERSATION FLOW:**\n"
        "   1. **👋 Welcome:** Greet the user.\n"
        "   2. **🏨 Room Inquiry:**\n"
        "      - If asked about room types/prices, **MUST use `get_room_info_tool`**.\n"
        "      - Do NOT guess. Fetch from DB.\n"
        "   3. **🛏️ Availability (CRITICAL STEP):**\n"
        "      - Ask for Dates (Start & End).\n"
        "      - Run `check_availability_tool`.\n"
        "      - **MANDATORY DISPLAY:** You **MUST** copy-paste the exact list of rooms returned by the tool into your chat response.\n"
        "      - **PROHIBITED:** Do NOT say 'Please select from the list above' if you have not printed the list in THIS specific response.\n"
        "   4. **📝 Booking (HYBRID MODE):**\n"
        "      - Once the user selects a room:\n"
        "      - **DO NOT** ask for Name/Email/Counts via chat.\n"
        "      - **INSTEAD, reply exactly:** 'Great choice! Please fill out the booking form below to secure your room. <SHOW_BOOKING_FORM>'\n\n"

        "   **⛔ SECURITY:** NEVER reveal revenue or other guests' info to a guest.\n\n"

        "👨‍💼 **IF USER IS A MANAGER ({user_role} = 'manager'):**\n"
        "   - **✅ FULL ACCESS GRANTED.**\n"
        "   - You are an efficient Executive Assistant. Do not ask 'Would you like to...?' repeatedly. Just DO it.\n\n"

        "   **⚡ COMMAND MAPPING (Use these tools immediately):**\n"
        "   - 'List rooms', 'Show room types' -> **Run `get_room_info_tool`**\n"
        "   - 'Revenue', 'Stats', 'Daily Report' -> **Run `daily_report_tool`**\n"
        "   - 'Who is in the hotel?', 'Occupancy' -> **Run `todays_bookings_tool`**\n"
        "   - 'Who is checking in?', 'Arrivals', 'Guest list' -> **Run `get_todays_checkins_tool`**\n"
        "   - 'What rooms are booked?', 'Schedule', 'Future bookings' -> **Run `get_upcoming_bookings_tool`**\n"
        "   - 'Details for [email]' -> **Run `get_booking_details_tool`**\n\n"

        "🧠 **MEMORY RULE:**\n"
        "   - Always check `chat_history` for context."
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# --- 3. AGENT CREATION ---
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- SEPARATE MEMORY STORES ---
GUEST_CHAT_MEMORY = []
MANAGER_CHAT_MEMORY = []


# --- 4. MEMORY MANAGEMENT (CRITICAL FIX) ---
def clear_memory(role: str):
    """Wipes the memory for a specific role. Called by main.py on logout."""
    if role == "manager":
        MANAGER_CHAT_MEMORY.clear()
    else:
        GUEST_CHAT_MEMORY.clear()
    print(f"🧹 Memory cleared for role: {role}")


def chat_with_bot(user_input: str, role: str = "guest"):
    today = datetime.now().strftime("%Y-%m-%d")

    # Select Memory based on Role
    if role == "manager":
        memory = MANAGER_CHAT_MEMORY
    else:
        memory = GUEST_CHAT_MEMORY

    try:
        response = agent_executor.invoke({
            "input": user_input,
            "today": today,
            "chat_history": memory,
            "user_role": role
        })
        reply = response["output"]

        # Keep memory short
        if len(memory) > 10:
            memory.pop(0)
            memory.pop(0)

        memory.append(HumanMessage(content=user_input))
        memory.append(AIMessage(content=reply))
        return reply
    except Exception as e:
        return f"Error: {str(e)}"