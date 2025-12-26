from datetime import datetime
from typing import Optional  # <--- 1. ADD THIS IMPORT
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.db.models import Booking, Room, Guest


@tool
def get_booking_details_tool(room_number: Optional[str] = None):  # <--- 2. CHANGE THIS LINE
    """
    Fetches booking details for the Manager.
    - If 'room_number' is provided (e.g. "101"), shows who booked that specific room and when.
    - If NO room_number is provided (or None), shows a list of ALL active and upcoming bookings.
    """
    db = SessionLocal()
    try:
        today = datetime.now().date()

        # Start the query
        query = db.query(Booking).join(Room).join(Guest)

        # FILTER: Show only Active (Currently in-house) or Future bookings
        query = query.filter(Booking.check_out_date >= today)

        # OPTIONAL FILTER: Specific Room
        if room_number:
            query = query.filter(Room.room_number == room_number)
            header = f"📅 **Schedule for Room {room_number}**"
        else:
            header = "📅 **All Active & Upcoming Bookings**"

        bookings = query.order_by(Booking.check_in_date).all()

        if not bookings:
            return "No active or upcoming bookings found."

        # Format the Output
        report_lines = [header]
        for b in bookings:
            status = "Unknown"
            if b.check_in_date.date() <= today < b.check_out_date.date():
                status = "🟢 In-House"
            elif b.check_in_date.date() > today:
                status = "🟡 Upcoming"
            elif b.check_out_date.date() == today:
                status = "🔴 Departing Today"

            report_lines.append(
                f"- **{b.check_in_date.strftime('%Y-%m-%d')}** to **{b.check_out_date.strftime('%Y-%m-%d')}**\n"
                f"  Room {b.room.room_number} ({b.room.room_type}) | Guest: {b.guest.name} ({b.guest.email}) | Status: {status}"
            )

        return "\n".join(report_lines)

    except Exception as e:
        return f"Error fetching bookings: {str(e)}"
    finally:
        db.close()