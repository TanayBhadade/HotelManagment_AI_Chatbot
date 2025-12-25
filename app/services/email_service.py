import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailService:
    def __init__(self):
        # Load credentials from .env
        self.sender_email = os.getenv("EMAIL_USER")
        self.sender_password = os.getenv("EMAIL_PASSWORD")
        self.manager_email = os.getenv("MANAGER_EMAIL", "admin@grandhotel.com")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def _send(self, to_email: str, subject: str, body: str):
        """Internal helper to send email or mock it."""

        # 1. MOCK MODE (If no credentials in .env, just print it)
        if not self.sender_email or not self.sender_password:
            print("=" * 60)
            print(f"📧 [MOCK EMAIL] To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}")
            print("=" * 60)
            return True

        # 2. REAL MODE (Sends actual email)
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
        subject = f"Booking Confirmation - Room {room}"
        body = f"""Dear {name},

We are delighted to confirm your stay at Grand Hotel.

Details:
- Room: {room}
- Check-in: {start}
- Check-out: {end}

See you soon!
Grand Hotel Concierge"""
        return self._send(email, subject, body)

    def send_manager_alert(self, name: str, room: str, start: str):
        subject = f"🚨 New Booking: Room {room}"
        body = f"Guest {name} has just booked Room {room} starting {start}."
        return self._send(self.manager_email, subject, body)