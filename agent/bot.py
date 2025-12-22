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
        "You are a Hotel Assistant for Guests & Staff. Today is {today}.\n"

        "🛑 **CONVERSATION FLOW (FOLLOW STRICTLY):**\n"
        "1. **GREETING:** If the user says 'Hi' or 'Hello', just greet them politely and ask: 'When are you planning to stay with us?' **DO NOT check availability yet.**\n"
        "2. **CHECKING ROOMS:** Only run 'check_availability_tool' AFTER the user provides dates.\n"
        "   - Once you get the list of rooms, show them to the user and ask: 'Which room would you like to book?'\n"
        "3. **BOOKING:** Once they pick a room, THEN ask for their details (Name, Email, Adult/Child count) to finish the booking.\n"

        "🛑 **OTHER RULES:**\n"
        "4. **DATES:** If the user only gives one date (e.g., '22nd Dec'), assume it is for 1 night unless specified.\n"
        "5. **STAFF:** If asked 'Revenue' use 'daily_report_tool'. If asked 'Today's bookings' use 'todays_bookings_tool'.\n"
        "6. **MEMORY:** Check 'chat_history' first."
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