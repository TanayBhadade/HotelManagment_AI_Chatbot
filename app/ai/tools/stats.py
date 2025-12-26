from datetime import datetime
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.db.models import Room, Booking


@tool
def hotel_stats_tool(**kwargs):
    """
    Fetches the current 'Daily Status Report' for the hotel.
    Returns:
    - Occupancy Rate (Percentage of rooms taken)
    - Total Revenue (Price of all currently occupied rooms)
    - Total Guests (Number of people currently in the hotel)

    Use this when the manager asks: 'Status report', 'How are we doing?', 'Occupancy?', or 'Revenue today'.
    """
    db = SessionLocal()
    try:
        today = datetime.now().date()

        # 1. Total Capacity
        total_rooms = db.query(Room).count()
        if total_rooms == 0:
            return "Error: No rooms configured in the database."

        # 2. Find Active Bookings (Guests inside the hotel RIGHT NOW)
        # Logic: Booking starts on or before today, and ends after today
        active_bookings = db.query(Booking).filter(
            Booking.check_in_date <= today,
            Booking.check_out_date > today
        ).all()

        occupied_count = len(active_bookings)
        occupancy_rate = (occupied_count / total_rooms) * 100

        # 3. Calculate Revenue (Sum of prices of occupied rooms)
        current_revenue = 0
        total_guests = 0

        for booking in active_bookings:
            # We need to fetch the room price for each booking
            room = db.query(Room).filter(Room.id == booking.room_id).first()
            if room:
                current_revenue += room.price

            # Count people
            total_guests += (booking.adults + booking.children)

        # 4. Format the Report
        return (
            f"  **Daily Hotel Pulse ({today})**\n"
            f"- **Occupancy:** {occupancy_rate:.1f}% ({occupied_count}/{total_rooms} rooms)\n"
            f"- **Current Revenue:** Rs. {current_revenue:,.2f} (Daily Run Rate)\n"
            f"- **Guests In-House:** {total_guests}\n"
        )

    except Exception as e:
        return f"Error generating stats: {str(e)}"
    finally:
        db.close()