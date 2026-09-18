import sqlite3
import os
from datetime import datetime

# Support Vercel serverless environment (/tmp is writable, root is read-only)
if os.environ.get("VERCEL") or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK):
    DB_PATH = "/tmp/cab_booking.db"
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cab_booking.db")

def get_db():
    need_init = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if need_init:
        init_db_conn(conn)
    return conn

def init_db():
    conn = get_db()
    init_db_conn(conn)
    conn.close()

def init_db_conn(conn):
    cursor = conn.cursor()
    
    # Driver profile & cab configuration table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS driver_config (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        car_model TEXT NOT NULL,
        car_number TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT NOT NULL,
        per_km_rate REAL NOT NULL,
        seats INTEGER DEFAULT 6,
        is_online INTEGER DEFAULT 1,
        rating REAL DEFAULT 4.9,
        trips_completed INTEGER DEFAULT 486
    );
    """)

    # Populate default driver config if empty
    cursor.execute("SELECT COUNT(*) FROM driver_config")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO driver_config (id, name, car_model, car_number, mobile, email, per_km_rate, seats, is_online, rating, trips_completed)
            VALUES (1, 'Manoj Mane', 'Maruti Suzuki Ertiga', 'MH12 TV 1292', '+91 9975222099', 'manojmane155@gmail.com', 15.0, 6, 1, 4.9, 486)
        """)

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        mobile TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # OTP table for verification
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_codes (
        mobile TEXT PRIMARY KEY,
        otp TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_ref TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        user_name TEXT NOT NULL,
        user_mobile TEXT NOT NULL,
        pickup_location TEXT NOT NULL,
        drop_location TEXT NOT NULL,
        distance_km REAL NOT NULL,
        rate_per_km REAL NOT NULL,
        fare_amount REAL NOT NULL,
        onboard_date TEXT NOT NULL,
        onboard_time TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        payment_status TEXT NOT NULL,
        booking_status TEXT NOT NULL,
        cancel_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cancelled_at TIMESTAMP
    );
    """)

    # Driver notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER,
        booking_ref TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        recipient_mobile TEXT NOT NULL,
        recipient_email TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
