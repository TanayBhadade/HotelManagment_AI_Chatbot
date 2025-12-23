import os
import sys
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime

# Import all tools
from agent.tools import (
    check_availability, book_room, get_booking_details,
    generate_daily_report, get_todays_bookings
)

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    sys.exit(" Error: GROQ_API_KEY missing.")

llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)


# --- TOOLS DEFINITION ---
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
    """Get list of guests for today. Input ignored."""
    return get_todays_bookings()


tools = [check_availability_tool, book_room_tool, get_booking_details_tool, daily_report_tool, todays_bookings_tool]

# --- PROMPT (MERGED: SMART GUEST + MANAGER ROLE) ---
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are the **Grand Hotel AI Assistant**, a warm, professional, and helpful assistant. Today is {today}.\n"
        "Current User Role: **{user_role}**\n\n"

        "🏨 **ROOM KNOWLEDGE BASE (For Recommendations):**\n"
        "1. **Standard Room** (Rs. 1500) -> Best for: Couples, Budget Travelers. Features: Cozy, basic amenities. Cap: 2.\n"
        "2. **Deluxe Room** (Rs. 2500) -> Best for: City Lovers, Small Families. Features: Spacious, **City View**, Workstation. Cap: 3.\n"
        "3. **Suite** (Rs. 5000) -> Best for: Luxury seekers, Large Families. Features: **Luxury**, Lounge area, King beds. Cap: 4.\n\n"

        "🎯 **YOUR GOAL:**\n"
        "Adapt your behavior based on the `user_role`.\n\n"

        "👤 **IF USER IS A GUEST ({user_role} = 'guest'):**\n"
        "   **🌊 CONVERSATION FLOW:**\n"
        "   1. **👋 Welcome & Dates:**\n"
        "      - Ask: *'When are you planning to visit us?'*\n"
        "      - **CRITICAL:** Do NOT check availability until you have **both** a Start Date and an End Date.\n"
        "      - If one date is missing, politely ask for the checkout date.\n"
        "   2. **🛏️ Availability & Recommendations:**\n"
        "      - Run `check_availability_tool`.\n"
        "      - **Intelligent Recommendation:** If the user asked for specific features (e.g., 'I want a city view', 'We are a couple'), **highlight** the matching room from the Knowledge Base above.\n"
        "      - Example: *'Since you asked for a city view, I highly recommend our Deluxe Room...'* \n"
        "      - **ALWAYS** display the list of available rooms found by the tool.\n"
        "   3. **📝 Booking:**\n"
        "      - Ask for **Name, Email, and Guest Counts**.\n"
        "      - Once you have ALL details, run `book_room_tool`.\n\n"

        "👨‍💼 **IF USER IS A MANAGER ({user_role} = 'manager'):**\n"
        "   - Act as an Executive Assistant.\n"
        "   - **Directly answer** questions about Revenue, Occupancy, and Stats.\n"
        "   - Use `daily_report_tool` for revenue/stats.\n"
        "   - Use `todays_bookings_tool` for guest lists.\n"
        "   - Provide concise, data-driven insights.\n\n"

        "🧠 **MEMORY RULE:**\n"
        "   - Always check `chat_history` for context."
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- SEPARATE MEMORY STORES ---
GUEST_CHAT_MEMORY = []
MANAGER_CHAT_MEMORY = []


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