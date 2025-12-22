from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# --- NEW: USER MODEL FOR AUTHENTICATION ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "manager" or "guest"

# --- EXISTING MODELS ---
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, index=True)
    room_type = Column(String)
    price = Column(Float)
    description = Column(String)
    capacity = Column(Integer, default=2)

    bookings = relationship("Booking", back_populates="room")

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)

    bookings = relationship("Booking", back_populates="guest")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    guest_id = Column(Integer, ForeignKey("guests.id"))
    check_in_date = Column(DateTime)
    check_out_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="confirmed")
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)

    room = relationship("Room", back_populates="bookings")
    guest = relationship("Guest", back_populates="bookings")