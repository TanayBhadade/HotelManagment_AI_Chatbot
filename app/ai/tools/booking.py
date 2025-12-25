from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.services.booking_service import BookingService


@tool
def book_room_tool(
        room_number: str,
        name: str,
        email: str,
        start_date: str,
        end_date: str,
        adults: str = "1",  # <--- CHANGED TO STRING
        children: str = "0"  # <--- CHANGED TO STRING
):
    """
    Books a room for a guest.
    - room_number: The room ID (e.g. "101")
    - dates: YYYY-MM-DD
    - adults/children: Numbers as strings (e.g. "2")
    """
    db = SessionLocal()
    try:
        service = BookingService(db)

        # 🛡️ LOGIC: We accept String to satisfy the API,
        # but convert to Int for the Database.
        safe_adults = int(adults)
        safe_children = int(children)

        return service.book_room(
            room_number=room_number,
            name=name,
            email=email,
            start_str=start_date,
            end_str=end_date,
            adults=safe_adults,
            children=safe_children
        )
    except ValueError:
        return "Error: Adults and Children must be valid numbers (e.g. '2')."
    except Exception as e:
        return f"Error processing booking: {str(e)}"
    finally:
        db.close()