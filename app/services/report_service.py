from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Booking, Room
from app.services.email_service import EmailService
from datetime import datetime


class ReportService:
    def __init__(self):
        self.emailer = EmailService()

    def generate_and_send(self):
        """Generates stats and emails the manager."""
        db = SessionLocal()
        try:
            # 1. Gather Stats (Simple Logic)
            total_rooms = db.query(Room).count()
            total_bookings = db.query(Booking).count()

            # Get today's bookings
            # (Assuming Booking has a 'created_at' or we just list all active)
            # For MVP, we list ALL active bookings
            bookings = db.query(Booking).all()

            report_lines = []
            report_lines.append(f"Total Rooms: {total_rooms}")
            report_lines.append(f"Total Bookings: {total_bookings}")
            report_lines.append("-" * 20)

            for b in bookings:
                report_lines.append(f"• Booking #{b.id}: Room {b.room_id} | Guest {b.guest_id}")

            final_report = "\n".join(report_lines)

            # 2. Send Email
            print(f"Generating Daily Report...")
            self.emailer.send_daily_report(final_report)
            print(f"Daily Report sent to Manager.")

        except Exception as e:
            print(f" Failed to send report: {e}")
        finally:
            db.close()