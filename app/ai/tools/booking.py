from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.services.booking_service import BookingService

@tool
def book_room_tool(room_number: str, name: str, email: str, start_date: str, end_date: str, adults: int = 1, children: int = 0):
    """
    Books a room.
    Use this ONLY after availability is confirmed.
    Requires: room_number, name, email, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD).
    """
    db = SessionLocal()
    try:
        service = BookingService(db)
        return service.book_room(room_number, name, email, start_date, end_date, adults, children)
    finally:
        db.close()