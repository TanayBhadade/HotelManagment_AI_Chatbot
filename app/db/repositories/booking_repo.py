from sqlalchemy.orm import Session
from app.db.models import Booking, Room, Guest
from datetime import datetime


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_overlapping_bookings(self, start_date: datetime, end_date: datetime):
        """Finds any booking that conflicts with the requested dates."""
        return self.db.query(Booking).filter(
            Booking.check_in_date < end_date,
            Booking.check_out_date > start_date
        ).all()

    def get_available_rooms(self, start_date: datetime, end_date: datetime):
        """Returns a list of Room objects that are free."""
        # 1. Find bad rooms
        overlapping = self.get_overlapping_bookings(start_date, end_date)
        booked_ids = [b.room_id for b in overlapping]

        # 2. Return good rooms (NOT IN bad list)
        return self.db.query(Room).filter(Room.id.notin_(booked_ids)).all()

    def create_booking(self, room_id: int, guest_id: int, start: datetime, end: datetime, adults: int, children: int):
        """Creates and saves a new booking."""
        new_booking = Booking(
            room_id=room_id,
            guest_id=guest_id,
            check_in_date=start,
            check_out_date=end,
            adults=adults,
            children=children,
            status="confirmed"
        )
        self.db.add(new_booking)
        self.db.commit()
        self.db.refresh(new_booking)
        return new_booking

    def get_guest_by_email(self, email: str):
        return self.db.query(Guest).filter(Guest.email == email).first()

    def create_guest(self, name: str, email: str):
        guest = Guest(name=name, email=email, phone="N/A")
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest