from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.booking_service import BookingService

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BookingRequest(BaseModel):
    room_number: str
    name: str
    email: str
    start_date: str
    end_date: str
    adults: int = 1
    children: int = 0


@router.post("/book")
def create_booking(req: BookingRequest, db: Session = Depends(get_db)):
    service = BookingService(db)
    result = service.book_room(
        req.room_number,
        req.name,
        req.email,
        req.start_date,
        req.end_date,
        req.adults,
        req.children
    )

    if "Error" in result:
        raise HTTPException(status_code=400, detail=result)

    return {"status": "success", "message": result}