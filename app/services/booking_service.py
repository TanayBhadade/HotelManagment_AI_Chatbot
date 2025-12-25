from sqlalchemy.orm import Session
from app.db.repositories.booking_repo import BookingRepository
from app.db.models import Room
from app.services.email_service import EmailService  # <--- IMPORTED
from dateutil import parser
from datetime import datetime


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BookingRepository(db)
        self.emailer = EmailService()  # <--- INITIALIZED

    def check_availability(self, start_str: str, end_str: str) -> str:
        try:
            start = parser.parse(start_str)
            end = parser.parse(end_str)
        except (ValueError, TypeError):
            return "Error: Invalid date format. Please use YYYY-MM-DD."


        # We compare the "date" part only (ignoring time)
        if start.date() < datetime.now().date():
            return f"Error: You cannot book dates in the past. Today is {datetime.now().strftime('%Y-%m-%d')}."

        # 🛑 NEW RULE: End date must be after Start date
        if end <= start:
            return "Error: Check-out date must be after Check-in date."

        # ... Existing Logic (Database Query) ...
        available_rooms = self.repo.get_available_rooms(start, end)

        if not available_rooms:
            return "No rooms available for these dates."

        response = ["Available Rooms:"]
        for room in available_rooms:
            response.append(
                f"- Room {room.room_number} ({room.room_type}): Rs. {room.price} | {room.description}"
            )

        return "\n".join(response)

    def book_room(self, room_number: str, name: str, email: str, start_str: str, end_str: str, adults=1, children=0):
        try:
            start = parser.parse(start_str)
            end = parser.parse(end_str)
        except:
            return "Error: Invalid date format."

        # 1. Verify Room
        room = self.db.query(Room).filter(Room.room_number == room_number).first()
        if not room:
            return f"Error: Room {room_number} does not exist."

        # 2. Check Capacity
        if (int(adults) + int(children)) > room.capacity:
            return f"Error: Room capacity exceeded (Max {room.capacity})."

        # 3. Double Check Availability
        conflicts = self.repo.get_overlapping_bookings(start, end)
        for booking in conflicts:
            if booking.room_id == room.id:
                return f"Error: Room {room_number} is already booked for these dates."

        # 4. Handle Guest
        guest = self.repo.get_guest_by_email(email)
        if not guest:
            guest = self.repo.create_guest(name, email)

        # 5. Create Booking
        booking = self.repo.create_booking(room.id, guest.id, start, end, adults, children)

        # 6. SEND EMAIL
        # ✅ ONLY send to Guest (Manager gets the Daily Report at 12 PM)
        self.emailer.send_guest_confirmation(name, email, room_number, start_str, end_str)

        return f"Success! Booking #{booking.id} confirmed. Confirmation email sent to {email}."