import sqlite3

# Connect to the database
conn = sqlite3.connect("hotel.db")
cursor = conn.cursor()

# List all tables
print("--- TABLES ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

# Example: Print all Users
print("\n--- BOOKINGS ---")
try:
    cursor.execute("SELECT * FROM  bookings")
    users = cursor.fetchall()
    for user in users:
        print(user)
except:
    print("Users table not found (did you run init_db.py?)")

conn.close()