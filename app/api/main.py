import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import engine, Base
from app.api.v1.routers import chat, bookings
from app.services.report_service import ReportService  # <--- NEW IMPORT

# Create Tables
Base.metadata.create_all(bind=engine)

# --- SCHEDULER SETUP ---
scheduler = BackgroundScheduler()
report_service = ReportService()


def run_daily_report():
    """Wrapper function for the scheduler"""
    report_service.generate_and_send()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🟢 STARTUP LOGIC
    print("🚀 Server Starting... Sending Manager Report...")
    run_daily_report()  # <--- 1. Send immediately on start

    print("⏰ Starting Scheduler (Daily at 12:00 PM)...")
    # <--- 2. Schedule for 12:00 PM everyday
    scheduler.add_job(run_daily_report, 'cron', hour=12, minute=0)
    scheduler.start()

    yield

    # 🔴 SHUTDOWN LOGIC
    print("🛑 Server Stopping... Killing Scheduler")
    scheduler.shutdown()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# --- ROUTERS ---
app.include_router(chat.router, tags=["Chat"])
app.include_router(bookings.router, tags=["Bookings"])


@app.get("/")
def health_check():
    return {"status": "running", "project": settings.PROJECT_NAME}


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8001, reload=True)