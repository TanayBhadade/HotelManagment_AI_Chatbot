from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.db.models import Guest, Booking


@tool
def get_guest_info_tool(email: str):
    """
    Fetches all information about a guest including their booking history using their email.
    """
    db = SessionLocal()
    try:
        guest = db.query(Guest).filter(Guest.email == email).first()
        if not guest:
            return f"No guest found with email: {email}"

        bookings = db.query(Booking).filter(Booking.guest_id == guest.id).all()
        booking_list = "\n".join(
            [f"- Room {b.room_id}: {b.check_in_date} to {b.check_out_date} ({b.status})" for b in bookings])

        return (f"Name: {guest.name}\n"
                f"Email: {guest.email}\n"
                f"Phone: {guest.phone}\n"
                f"Booking History:\n{booking_list if booking_list else 'No history'}")
    finally:
        db.close()