import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from database.connection import engine, SessionLocal
from database.models import Base, Room, Guest, Booking, User
from auth import hash_password  # Import our new auth tool


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def reset_database():
    """Drops all tables and creates new ones."""
    try:
        logger.info("🗑️  Dropping old database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✨ Creating new schema...")
        Base.metadata.create_all(bind=engine)
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Database Reset Failed: {e}")
        return False


def seed_users(db):
    """Creates default Admin and Guest users."""
    logger.info("🔐 Seeding Users...")

    # 1. Manager Account
    manager = User(
        username="manager",
        email="admin@grandhotel.com",
        hashed_password=hash_password("admin123"),  # Default Password
        role="manager"
    )

    # 2. Guest Account
    guest = User(
        username="guest",
        email="guest@example.com",
        hashed_password=hash_password("guest123"),  # Default Password
        role="guest"
    )

    db.add_all([manager, guest])
    db.commit()
    logger.info("✅ Users created: 'manager' (pass: admin123) and 'guest' (pass: guest123)")


def seed_rooms(db):
    """Populates room inventory."""
    room_config = [
        {"type": "Standard Queen", "price": 1400.0, "capacity": 2, "count": 6,
         "desc": "Cozy queen bed, great for couples."},
        {"type": "Standard Twin", "price": 1450.0, "capacity": 2, "count": 4,
         "desc": "Two twin beds, perfect for friends."},
        {"type": "Deluxe King", "price": 2600.0, "capacity": 3, "count": 5,
         "desc": "King bed with city view and a lounge chair."},
        {"type": "Deluxe Family", "price": 3200.0, "capacity": 4, "count": 4,
         "desc": "King + sofa bed, mini living area—family friendly."},
        {"type": "Executive", "price": 3800.0, "capacity": 2, "count": 3,
         "desc": "Quiet floor, workspace, premium amenities."},
        {"type": "Studio Suite", "price": 4200.0, "capacity": 3, "count": 3,
         "desc": "Open-plan suite with seating area."},
        {"type": "One-Bedroom Suite", "price": 5200.0, "capacity": 4, "count": 2,
         "desc": "Separate bedroom + living room, great for longer stays."},
        {"type": "Accessible King", "price": 2400.0, "capacity": 2, "count": 2,
         "desc": "Accessible layout, roll-in shower, wider clearances."},
        {"type": "Penthouse", "price": 9500.0, "capacity": 4, "count": 1,
         "desc": "Top-floor luxury, terrace, sweeping views."},
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
    logger.info(f"✅ Seeded {len(rooms_to_add)} rooms.")


def main():
    if not reset_database():
        sys.exit(1)

    db = SessionLocal()
    try:
        seed_rooms(db)
        seed_users(db)  # <--- New Step
        logger.info("🚀 Database Ready! Login with 'manager'/'admin123'")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()