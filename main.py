from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.bot import chat_with_bot
from agent.tools import save_daily_report_pdf, send_report_email  # Added import
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
import datetime


# --- CONFIG ---
class ChatRequest(BaseModel):
    message: str


app = FastAPI(title="Hotel AI API")


# --- SCHEDULER TASK ---
def generate_scheduled_pdf():
    """Runs at 12:00 PM to save PDF report and email it."""
    print("\n📄 [SYSTEM] Generating Daily PDF Report...")
    try:
        # 1. Generate PDF
        path = save_daily_report_pdf()
        print(f"✅ Report saved: {path}")

        # 2. Send Email
        print("📧 [SYSTEM] Sending Email to Manager...")
        email_sent = send_report_email(path)
        if email_sent:
            print("✅ Email sent successfully.")
        else:
            print("❌ Failed to send email.")

    except Exception as e:
        print(f"❌ Report/Email Error: {e}")


scheduler = BackgroundScheduler()
# Schedule for 12:00 PM Daily
scheduler.add_job(generate_scheduled_pdf, 'cron', hour=12, minute=0)
# Run immediately + 5 seconds for TESTING
scheduler.add_job(generate_scheduled_pdf, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=5))
scheduler.start()


# --- ENDPOINTS ---
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return {"response": chat_with_bot(request.message)}


@app.post("/trigger-report")
async def trigger_report():
    generate_scheduled_pdf()
    return {"status": "PDF Generated & Emailed"}


if __name__ == "__main__":
    print("🚀 Server starting on Port 8001...")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)