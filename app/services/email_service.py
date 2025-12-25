import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.sender_email = settings.EMAIL_SENDER
        self.manager_email = settings.EMAIL_MANAGER or "admin@grandhotel.com"

        # ✅ FIX: Load from Settings, not os.getenv
        self.sender_password = settings.EMAIL_PASSWORD

        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT

    def _send(self, to_email: str, subject: str, body: str):
        """Internal helper to send email or mock it."""

        # MOCK MODE
        if not self.sender_email or not self.sender_password:
            print(f"\n{'=' * 20} 📧 EMAIL SIMULATION {'=' * 20}")
            print(f"FROM:    {self.sender_email or 'system@grandhotel.com'}")
            print(f"TO:      {to_email}")
            print(f"SUBJECT: {subject}")
            print(f"BODY:\n{body}")
            print(f"{'=' * 58}\n")
            return True

        # REAL MODE
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def send_guest_confirmation(self, name: str, email: str, room: str, start: str, end: str):
        subject = f"✅ Booking Confirmed - Room {room}"
        body = f"""Dear {name},

We are delighted to confirm your stay at Grand Hotel.

Details:
- Room: {room}
- Check-in: {start}
- Check-out: {end}

See you soon!
Grand Hotel Concierge"""
        return self._send(email, subject, body)

    def send_daily_report(self, report_content: str):
        """Sends the Daily Summary to the Manager."""
        subject = f"📊 Daily Hotel Report - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""DAILY OPERATIONS REPORT

Here is the summary of bookings and occupancy:

{report_content}

End of Report.
Grand Hotel System"""
        return self._send(self.manager_email, subject, body)