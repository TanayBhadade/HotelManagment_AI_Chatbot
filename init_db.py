import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from database.connection import engine, SessionLocal
from database.models import Base, Room, Guest, Booking

# --- CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def reset_database():
    """Drops all existing tables and creates new ones based on models."""
    try:
        logger.info("🗑️  Dropping old database tables...")
        Base.metadata.drop_all(bind=engine)

        logger.info("✨ Creating new schema (Rooms, Guests, Bookings)...")
        Base.metadata.create_all(bind=engine)
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Database Reset Failed: {e}")
        return False


def seed_rooms(db):
    """Populates the database with initial room inventory."""
    room_config = [
        {"type": "Standard", "price": 1500.0, "capacity": 2, "count": 5,
         "desc": "Cozy room for couples with basic amenities."},
        {"type": "Deluxe", "price": 2500.0, "capacity": 3, "count": 5,
         "desc": "Spacious room with city view and workstation."},
        {"type": "Suite", "price": 5000.0, "capacity": 4, "count": 2,
         "desc": "Luxury suite with two king beds and a lounge area."},
    ]

    rooms_to_add = []
    room_counter = 100

    for config in room_config:
        for _ in range(config["count"]):
            room_counter += 1
            new_room = Room(
                room_number=str(room_counter),
                room_type=config["type"],
                price=config["price"],
                capacity=config["capacity"],
                description=config["desc"]
            )
            rooms_to_add.append(new_room)

    db.add_all(rooms_to_add)
    db.commit()
    logger.info(f"✅ Seeded {len(rooms_to_add)} rooms into the database.")


def seed_guests_and_bookings(db):
    """Creates sample guests and initial bookings for testing."""
    # 1. Create Guests
    paras = Guest(name="Paras", email="paras@gmail.com", phone="9876543210")
    tanay = Guest(name="Tanay", email="tanay@example.com", phone="1234567890")
    manager = Guest(name="Test Manager", email="manager@hotel.com", phone="0000000000")

    db.add_all([paras, tanay, manager])
    db.commit()

    # Refresh to get IDs
    db.refresh(paras)
    db.refresh(tanay)

    # 2. Create Bookings
    # Paras: Room 101 (Standard), 2 Adults, 1 Child
    booking_1 = Booking(
        room_id=1,  # Assuming ID 1 is the first Standard room
        guest_id=paras.id,
        check_in_date=datetime.now(),
        check_out_date=datetime.now() + timedelta(days=3),
        adults=2,
        children=1,
        status="confirmed"
    )

    # Tanay: Room 106 (Deluxe), 1 Adult, 0 Children
    booking_2 = Booking(
        room_id=6,  # Assuming ID 6 is the first Deluxe room
        guest_id=tanay.id,
        check_in_date=datetime.now() + timedelta(days=5),
        check_out_date=datetime.now() + timedelta(days=7),
        adults=1,
        children=0,
        status="confirmed"
    )

    db.add_all([booking_1, booking_2])
    db.commit()
    logger.info("✅ Seeded sample guests and bookings.")


def main():
    """Main execution flow."""
    if not reset_database():
        sys.exit(1)

    db = SessionLocal()
    try:
        seed_rooms(db)
        seed_guests_and_bookings(db)
        logger.info("🚀 Database initialization complete! You are ready to demo.")
    except Exception as e:
        logger.error(f"❌ unexpected error during seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()