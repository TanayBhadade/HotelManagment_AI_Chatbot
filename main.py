from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.bot import chat_with_bot
from agent.tools import save_daily_report_pdf, book_room  # <--- Import book_room
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
import datetime

# --- CONFIG ---
class ChatRequest(BaseModel):
    message: str
    role: str = "guest"

# NEW: Booking Request Model
class BookingRequest(BaseModel):
    room_number: str
    name: str
    email: str
    start_date: str
    end_date: str
    adults: int = 1
    children: int = 0

app = FastAPI(title="Hotel AI API")

# --- SCHEDULER TASK (Unchanged) ---
def generate_scheduled_pdf():
    print("\n📄 [SYSTEM] Generating Daily PDF Report...")
    try:
        path = save_daily_report_pdf()
        print(f"✅ Report saved: {path}")
    except Exception as e:
        print(f"❌ Report/Email Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(generate_scheduled_pdf, 'cron', hour=12, minute=0)
scheduler.start()

# --- ENDPOINTS ---
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return {"response": chat_with_bot(request.message, request.role)}

@app.post("/book")
async def book_endpoint(req: BookingRequest):
    """Direct booking endpoint for the Streamlit Form"""
    result = book_room(
        req.room_number, req.name, req.email,
        req.start_date, req.end_date,
        req.adults, req.children
    )
    return {"status": result}

@app.post("/trigger-report")
async def trigger_report():
    generate_scheduled_pdf()
    return {"status": "PDF Generated & Emailed"}

if __name__ == "__main__":
    print("🚀 Server starting on Port 8001...")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)