from datetime import datetime
from database.connection import SessionLocal
from database.models import Room, Booking, Guest
from fpdf import FPDF
import os


# --- HELPER: PDF GENERATOR FOR RECEIPTS ---
def generate_guest_receipt(booking_id):
    """
    Generates a PDF receipt for a specific booking.
    """
    db = SessionLocal()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    guest = db.query(Guest).filter(Guest.id == booking.guest_id).first()

    # Calculate Total Cost
    nights = (booking.check_out_date - booking.check_in_date).days
    if nights < 1: nights = 1  # Minimum 1 night
    total_cost = room.price * nights

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="HOTEL BOOKING RECEIPT", ln=True, align='C')
    pdf.ln(10)

    # Details
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Booking ID: #{booking.id}", ln=True)
    pdf.cell(200, 10, txt=f"Guest Name: {guest.name}", ln=True)
    pdf.cell(200, 10, txt=f"Room: {room.room_number} ({room.room_type})", ln=True)
    pdf.cell(200, 10, txt=f"Dates: {booking.check_in_date.date()} to {booking.check_out_date.date()}", ln=True)
    pdf.ln(5)

    # Financials
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Rate per Night: Rs. {room.price}", ln=True)
    pdf.cell(200, 10, txt=f"Total Nights: {nights}", ln=True)
    pdf.cell(200, 10, txt=f"----------------------------------", ln=True)
    pdf.cell(200, 10, txt=f"TOTAL PAID: Rs. {total_cost}", ln=True)

    # Save
    if not os.path.exists("receipts"):
        os.makedirs("receipts")

    filename = f"receipt_{guest.name.replace(' ', '_')}_{booking.id}.pdf"
    filepath = os.path.join("receipts", filename)
    pdf.output(filepath)
    db.close()
    return filename


# --- TOOL 1: Check Availability ---
def check_availability(start_date: str, end_date: str):
    db = SessionLocal()
    try:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return "Date Error: Please use YYYY-MM-DD format (e.g., 2025-01-20)."

        overlapping_bookings = db.query(Booking).filter(
            Booking.check_in_date < end,
            Booking.check_out_date > start
        ).all()
        booked_ids = [b.room_id for b in overlapping_bookings]
        available_rooms = db.query(Room).filter(Room.id.notin_(booked_ids)).all()

        if not available_rooms:
            return "No rooms available for these dates."

        result = []
        for r in available_rooms:
            result.append(f"- **Room {r.room_number}** ({r.room_type}) - Rs.{r.price} (Cap: {r.capacity})")

        return "\n".join(result)
    except Exception as e:
        return f"Database Error: {str(e)}"
    finally:
        db.close()


# --- TOOL 2: Book Room (With Receipt Generation) ---
def book_room(room_number: str, name: str, email: str, start_date: str, end_date: str, adults=1, children=0):
    db = SessionLocal()
    try:
        try:
            adults = int(adults)
            children = int(children)
        except (ValueError, TypeError):
            return "Error: Adults and Children counts must be numbers."

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return "Date Error: Please use YYYY-MM-DD format."

        room = db.query(Room).filter(Room.room_number == room_number).first()
        if not room: return f"Error: Room {room_number} does not exist."

        # Capacity Check
        if (adults + children) > room.capacity:
            return f"Error: Room {room_number} only holds {room.capacity} people."

        # Availability Check
        is_taken = db.query(Booking).filter(
            Booking.room_id == room.id,
            Booking.check_in_date < end,
            Booking.check_out_date > start
        ).first()
        if is_taken: return f"Error: Room {room_number} is already booked."

        guest = db.query(Guest).filter(Guest.email == email).first()
        if not guest:
            guest = Guest(name=name, email=email, phone="N/A")
            db.add(guest)
            db.commit()
            db.refresh(guest)

        new_booking = Booking(
            room_id=room.id, guest_id=guest.id, check_in_date=start, check_out_date=end,
            status="confirmed", adults=adults, children=children
        )
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)  # Get ID for receipt

        # --- NEW: GENERATE RECEIPT ---
        receipt_file = generate_guest_receipt(new_booking.id)

        return f"Success! Room {room_number} booked for {name}. Receipt generated: {receipt_file}"

    except Exception as e:
        return f"Booking Failed: {str(e)}"
    finally:
        db.close()


# --- TOOL 3: Get Booking Details ---
def get_booking_details(email: str):
    db = SessionLocal()
    try:
        guest = db.query(Guest).filter(Guest.email == email).first()
        if not guest: return "No guest found with that email."
        bookings = db.query(Booking).filter(Booking.guest_id == guest.id).all()
        if not bookings: return f"No active bookings found for {email}."

        results = []
        for b in bookings:
            room = db.query(Room).filter(Room.id == b.room_id).first()
            results.append(
                f"Booking ID: {b.id} | Room: {room.room_number} | Dates: {b.check_in_date.date()} to {b.check_out_date.date()}")
        return "\n".join(results)
    finally:
        db.close()


# --- TOOL 4: Daily Report (Text) ---
def generate_daily_report():
    db = SessionLocal()
    try:
        today = datetime.now().date()
        total_bookings = db.query(Booking).count()
        total_guests = db.query(Guest).count()
        revenue = 0
        for b in db.query(Booking).all():
            if b.room: revenue += b.room.price

        return (
            f"DATE: {today}\n"
            f"Total Confirmed Bookings: {total_bookings}\n"
            f"Total Registered Guests: {total_guests}\n"
            f"Total Estimated Revenue: Rs. {revenue}\n"
        )
    finally:
        db.close()


# --- TOOL 5: Daily Report (PDF) ---
def save_daily_report_pdf():
    """Generates PDF for the Owner."""
    report_text = generate_daily_report()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Daily Business Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for line in report_text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)

    filename = f"daily_report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    if not os.path.exists("reports"): os.makedirs("reports")
    filepath = os.path.join("reports", filename)
    pdf.output(filepath)
    return filepath


# --- TOOL 6: Staff Dashboard ---
def get_todays_bookings():
    db = SessionLocal()
    try:
        today = datetime.now().date()
        active_bookings = db.query(Booking).filter(
            Booking.check_in_date <= today, Booking.check_out_date >= today
        ).all()

        if not active_bookings: return "No active bookings found for today."

        report = ["Today's Occupancy:"]
        for b in active_bookings:
            guest = db.query(Guest).filter(Guest.id == b.guest_id).first()
            room = db.query(Room).filter(Room.id == b.room_id).first()
            status = "Checking In" if b.check_in_date.date() == today else "In-House"
            report.append(f"- [{status}] Room {room.room_number}: {guest.name} ({b.adults}A, {b.children}C)")

        return "\n".join(report)
    finally:
        db.close()