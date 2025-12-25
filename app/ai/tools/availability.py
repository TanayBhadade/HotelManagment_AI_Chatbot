from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.services.booking_service import BookingService

@tool
def check_availability_tool(start_date: str, end_date: str):
    """
    Checks room availability for given dates.
    Input format: YYYY-MM-DD
    """
    db = SessionLocal()
    try:
        service = BookingService(db)
        return service.check_availability(start_date, end_date)
    finally:
        db.close()