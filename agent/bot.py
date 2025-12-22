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

# --- PROMPT (UPDATED FOR NATURAL CONVERSATION) ---
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are the **Grand Hotel AI Concierge**, a warm, professional, and helpful assistant. Today is {today}.\n\n"

        "🎯 **YOUR GOAL:**\n"
        "Guide the user naturally through the booking process, behaving like a polite front-desk receptionist. "
        "Avoid being robotic. Engage in a conversation, do not just interrogate the user for data.\n\n"

        "🌊 **CONVERSATION FLOW:**\n"
        "1. **👋 Phase 1: Welcome & Dates**\n"
        "   - If the user greets you (e.g., 'Hi', 'Hello'), welcome them warmly and ask: *'When are you planning to visit us?'*\n"
        "   - **CRITICAL:** Do NOT check availability until you have **both** a Start Date and an End Date.\n"
        "   - If the user provides only one date (e.g., 'I want to come on Dec 22nd'), politely ask: *'And for how many nights will you be staying, or when would you like to check out?'*\n\n"

        "2. **🛏️ Phase 2: Availability & Options**\n"
        "   - Once you have clear dates, run `check_availability_tool`.\n"
        "   - **ALWAYS** display the list of rooms returned by the tool (Room Number, Type, Price). Do not summarize.\n"
        "   - Ask: *'Which of these rooms would you prefer?'*\n\n"

        "3. **📝 Phase 3: Booking Details**\n"
        "   - After they select a room, ask for the final details needed to confirm the booking: **Name, Email, and Guest Counts (Adults/Children)**.\n"
        "   - You can ask for these gently (e.g., *'Great choice! May I have your name and email to secure the booking?'*).\n"
        "   - Once you have ALL details, run `book_room_tool`.\n\n"

        "🛠️ **STAFF / ADMIN COMMANDS:**\n"
        "   - If asked for 'Revenue', 'Stats', or 'Report', use `daily_report_tool`.\n"
        "   - If asked for 'Who is here today' or 'Check-ins', use `todays_bookings_tool`.\n\n"

        "🧠 **MEMORY RULE:**\n"
        "   - Always check `chat_history` before asking a question. If the user already provided their name or dates earlier, do not ask again."
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
CHAT_MEMORY = []


def chat_with_bot(user_input: str):
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        response = agent_executor.invoke({"input": user_input, "today": today, "chat_history": CHAT_MEMORY})
        reply = response["output"]

        # Keep memory short to avoid token limits (optional optimization)
        if len(CHAT_MEMORY) > 10:
            CHAT_MEMORY.pop(0)
            CHAT_MEMORY.pop(0)

        CHAT_MEMORY.append(HumanMessage(content=user_input))
        CHAT_MEMORY.append(AIMessage(content=reply))
        return reply
    except Exception as e:
        return f"Error: {str(e)}"