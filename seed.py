import logging
import sys
import hashlib


# CORRECT IMPORTS FOR NEW ARCHITECTURE
from app.db.session import engine, SessionLocal
from app.db.models import Base, Room, User
from sqlalchemy.exc import SQLAlchemyError
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def simple_hash(password: str):
    """A simple hash for demo purposes (SHA256)."""
    return hashlib.sha256(password.encode()).hexdigest()


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
        hashed_password=get_password_hash("admin123"),
        role="manager"
    )

    # 2. Guest Account
    guest = User(
        username="guest",
        email="guest@example.com",
        hashed_password=get_password_hash("guest123"),
        role="guest"
    )

    db.add_all([manager, guest])
    db.commit()
    logger.info("✅ Users created: 'manager' / 'guest'")


def seed_rooms(db):
    """Populates room inventory."""
    room_config = [
        {"type": "Standard Queen", "price": 1400.0, "capacity": 2, "count": 4,
         "desc": "Cozy queen bed, great for couples."},
        {"type": "Deluxe King", "price": 2600.0, "capacity": 3, "count": 3, "desc": "King bed with city view."},
        {"type": "Family Suite", "price": 4200.0, "capacity": 4, "count": 2, "desc": "Two beds + living area."},
        {"type": "Penthouse", "price": 9500.0, "capacity": 6, "count": 1, "desc": "Top floor luxury with terrace."},
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
        seed_users(db)
        logger.info("🚀 Database Ready! Login with 'manager' / 'admin123'")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()