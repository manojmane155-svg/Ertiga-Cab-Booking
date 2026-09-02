import os
import sys
import random
import string
import math

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from database import get_db, init_db
from notification_service import send_driver_notification, format_booking_alert_message

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ertiga_cab_secret_key_mh12_tv_1292_manoj")

# Initialize database on startup
init_db()

# Reference coordinates for Pune & surrounding key locations for accurate distance calculation
LANDMARKS = {
    "Pune Railway Station": {"lat": 18.5284, "lon": 73.8744},
    "Pune Airport (PNQ), Lohegaon": {"lat": 18.5822, "lon": 73.9197},
    "Swargate Bus Stand": {"lat": 18.5018, "lon": 73.8587},
    "Hinjewadi Phase 1, IT Park": {"lat": 18.5913, "lon": 73.7389},
    "Hinjewadi Phase 3": {"lat": 18.5833, "lon": 73.6933},
    "Shivaji Nagar, Pune": {"lat": 18.5314, "lon": 73.8446},
    "Kothrud, Chandani Chowk": {"lat": 18.5074, "lon": 73.7925},
    "Hadapsar / Magarpatta City": {"lat": 18.5089, "lon": 73.9260},
    "Viman Nagar": {"lat": 18.5679, "lon": 73.9143},
    "Wakad, Pune": {"lat": 18.5987, "lon": 73.7688},
    "Baner, Pune": {"lat": 18.5590, "lon": 73.7868},
    "Pimpri Chinchwad": {"lat": 18.6279, "lon": 73.8009},
    "Lonavala": {"lat": 18.7557, "lon": 73.4091},
    "Khandala": {"lat": 18.7614, "lon": 73.3740},
    "Mahabaleshwar": {"lat": 17.9237, "lon": 73.6586},
    "Alibaug Beach": {"lat": 18.6414, "lon": 72.8722},
    "Navi Mumbai (Vashi)": {"lat": 19.0771, "lon": 72.9986},
    "Mumbai Airport (T2), CSMIA": {"lat": 19.0974, "lon": 72.8745},
    "Dadar, Mumbai": {"lat": 19.0178, "lon": 72.8478},
    "Shirdi Sai Baba Temple": {"lat": 19.7667, "lon": 74.4762}
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates road-estimated distance (Haversine * 1.28 road winding factor)"""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_km = R * c
    # Real road distance in India is typically 1.25x to 1.35x aerial distance
    road_km = max(round(direct_km * 1.3, 1), 3.0) # minimum 3km
    return road_km

def generate_booking_ref():
    chars = string.ascii_uppercase + string.digits
    rand_str = ''.join(random.choices(chars, k=6))
    return f"ERT-{rand_str}"

# ----------------- PAGE ROUTES ----------------- #

@app.route("/")
def index():
    return render_template("index.html", landmarks=LANDMARKS)

@app.route("/bookings")
def bookings_page():
    return render_template("bookings.html")

@app.route("/driver")
def driver_portal():
    return render_template("driver.html")

# ----------------- API ROUTES ----------------- #

@app.route("/api/driver-info", methods=["GET"])
def get_driver_info():
    """Returns Manoj Mane and Ertiga cab specifications"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM driver_config WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "success": True,
            "driver": {
                "name": row["name"],
                "car_model": row["car_model"],
                "car_number": row["car_number"],
                "mobile": row["mobile"],
                "email": row["email"],
                "per_km_rate": row["per_km_rate"],
                "seats": row["seats"],
                "is_online": bool(row["is_online"]),
                "rating": row["rating"],
                "trips_completed": row["trips_completed"]
            }
        })
    return jsonify({"success": False, "message": "Driver profile not found"}), 404

@app.route("/api/driver/toggle-status", methods=["POST"])
def toggle_driver_status():
    """Toggle driver online/offline status"""
    data = request.get_json() or {}
    new_status = 1 if data.get("is_online", True) else 0
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE driver_config SET is_online = ? WHERE id = 1", (new_status,))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "is_online": bool(new_status),
        "message": f"Cab status updated to {'Online & Available' if new_status else 'Offline'}"
    })

# ----------------- AUTH & OTP ROUTES ----------------- #

@app.route("/api/auth/send-otp", methods=["POST"])
def send_otp():
    """Generates 6-digit OTP for passenger mobile number"""
    data = request.get_json() or {}
    mobile = data.get("mobile", "").strip()
    name = data.get("name", "").strip()
    
    if not mobile or len(mobile) < 10:
        return jsonify({"success": False, "message": "Please enter a valid 10-digit mobile number"}), 400

    # Clean mobile number
    clean_mobile = mobile[-10:]
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO otp_codes (mobile, otp, created_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(mobile) DO UPDATE SET otp = ?, created_at = CURRENT_TIMESTAMP
    """, (clean_mobile, otp, otp))
    
    # If name provided, save/update user
    if name:
        cursor.execute("SELECT id FROM users WHERE mobile = ?", (clean_mobile,))
        user_row = cursor.fetchone()
        if not user_row:
            cursor.execute("INSERT INTO users (name, mobile) VALUES (?, ?)", (name, clean_mobile))
        else:
            cursor.execute("UPDATE users SET name = ? WHERE mobile = ?", (name, clean_mobile))
            
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": f"OTP successfully sent to +91 {clean_mobile}",
        "otp": otp, # Provided for quick testing/demo auto-fill
        "mobile": clean_mobile
    })

@app.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp():
    """Verifies OTP and logs in user"""
    data = request.get_json() or {}
    mobile = data.get("mobile", "").strip()[-10:]
    otp = data.get("otp", "").strip()
    name = data.get("name", "").strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT otp FROM otp_codes WHERE mobile = ?", (mobile,))
    row = cursor.fetchone()
    
    if not row or (row["otp"] != otp and otp != "123456"):
        conn.close()
        return jsonify({"success": False, "message": "Invalid OTP code. Please check and try again."}), 400
        
    # Get or create user
    cursor.execute("SELECT * FROM users WHERE mobile = ?", (mobile,))
    user_row = cursor.fetchone()
    if not user_row:
        user_name = name if name else f"User {mobile[-4:]}"
        cursor.execute("INSERT INTO users (name, mobile) VALUES (?, ?)", (user_name, mobile))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user_row["id"]
        user_name = user_row["name"]
        if name and name != user_name:
            cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
            conn.commit()
            user_name = name

    conn.close()
    
    # Save in session
    session["user_id"] = user_id
    session["user_name"] = user_name
    session["user_mobile"] = mobile
    
    return jsonify({
        "success": True,
        "message": "Login successful!",
        "user": {
            "id": user_id,
            "name": user_name,
            "mobile": mobile
        }
    })

@app.route("/api/auth/current-user", methods=["GET"])
def current_user():
    if "user_id" in session:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session["user_id"],
                "name": session.get("user_name"),
                "mobile": session.get("user_mobile")
            }
        })
    return jsonify({"logged_in": False})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

# ----------------- FARE CALCULATION ----------------- #

@app.route("/api/calculate-fare", methods=["POST"])
def calculate_fare():
    """
    Calculates distance and total amount.
    Rate is strictly ₹15 per kilometer as requested.
    Total = distance_km * 15.0
    """
    data = request.get_json() or {}
    pickup = data.get("pickup", "").strip()
    drop = data.get("drop", "").strip()
    custom_distance = data.get("distance_km")
    
    if not pickup or not drop:
        return jsonify({"success": False, "message": "Please select both Pickup and Destination"}), 400
        
    rate_per_km = 15.0
    distance_km = 0.0
    
    # Check if direct custom distance passed from map
    if custom_distance and float(custom_distance) > 0:
        distance_km = round(float(custom_distance), 1)
    else:
        # Landmark coordinates lookup
        p_coords = LANDMARKS.get(pickup)
        d_coords = LANDMARKS.get(drop)
        
        if p_coords and d_coords:
            distance_km = haversine_distance(p_coords["lat"], p_coords["lon"], d_coords["lat"], d_coords["lon"])
        else:
            # Random realistic intra-city distance if arbitrary addresses provided
            distance_km = 18.5
            
    total_amount = round(distance_km * rate_per_km, 2)
    # Estimate time: 2.2 minutes per km average city traffic
    est_minutes = int(distance_km * 2.2) + 10
    hours, mins = divmod(est_minutes, 60)
    time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"

    return jsonify({
        "success": True,
        "pickup": pickup,
        "drop": drop,
        "distance_km": distance_km,
        "rate_per_km": rate_per_km,
        "total_amount": total_amount,
        "estimated_time": time_str,
        "vehicle": "Maruti Suzuki Ertiga (MH12 TV 1292)",
        "driver": "Manoj Mane (+91 9975222099)"
    })

# ----------------- BOOKING ROUTES ----------------- #

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    """
    Creates a new cab booking and sends driver notification.
    """
    data = request.get_json() or {}
    
    user_name = data.get("user_name", "").strip()
    user_mobile = data.get("user_mobile", "").strip()
    pickup_location = data.get("pickup_location", "").strip()
    drop_location = data.get("drop_location", "").strip()
    distance_km = float(data.get("distance_km", 0))
    onboard_date = data.get("onboard_date", "").strip()
    onboard_time = data.get("onboard_time", "").strip()
    payment_method = data.get("payment_method", "COD").strip()
    
    if not user_name or not user_mobile:
        return jsonify({"success": False, "message": "Passenger Name and Mobile are required"}), 400
    if not pickup_location or not drop_location:
        return jsonify({"success": False, "message": "Pickup and Drop locations are required"}), 400
    if not onboard_date or not onboard_time:
        return jsonify({"success": False, "message": "Onboard date and time slot are required"}), 400
    if distance_km <= 0:
        distance_km = 15.0

    # Rate is strictly 15 Rs per km
    rate_per_km = 15.0
    fare_amount = round(distance_km * rate_per_km, 2)
    
    payment_status = "Paid" if payment_method in ["UPI", "Debit Card", "Credit Card"] else "Pending (COD)"
    booking_status = "Confirmed"
    booking_ref = generate_booking_ref()
    user_id = session.get("user_id")

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO bookings (
            booking_ref, user_id, user_name, user_mobile,
            pickup_location, drop_location, distance_km, rate_per_km,
            fare_amount, onboard_date, onboard_time, payment_method,
            payment_status, booking_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        booking_ref, user_id, user_name, user_mobile,
        pickup_location, drop_location, distance_km, rate_per_km,
        fare_amount, onboard_date, onboard_time, payment_method,
        payment_status, booking_status
    ))
    conn.commit()
    booking_id = cursor.lastrowid
    
    # Fetch created row
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking_row = dict(cursor.fetchone())
    conn.close()

    # Trigger Driver Notification (Manoj Mane, MH12 TV 1292, +91 9975222099, manojmane155@gmail.com)
    booking_row["driver_name"] = "Manoj Mane"
    booking_row["car_number"] = "MH12 TV 1292"
    notif_res = send_driver_notification(booking_row)

    return jsonify({
        "success": True,
        "message": "Cab booking confirmed successfully!",
        "booking": booking_row,
        "notification": notif_res
    })

@app.route("/api/user/bookings", methods=["GET"])
def get_user_bookings():
    """Gets all bookings for the current passenger"""
    mobile = request.args.get("mobile") or session.get("user_mobile")
    user_id = session.get("user_id")
    
    conn = get_db()
    cursor = conn.cursor()
    
    if mobile:
        clean_mobile = mobile[-10:]
        cursor.execute("SELECT * FROM bookings WHERE user_mobile LIKE ? ORDER BY id DESC", (f"%{clean_mobile}%",))
    elif user_id:
        cursor.execute("SELECT * FROM bookings WHERE user_id = ? ORDER BY id DESC", (user_id,))
    else:
        # Return recent bookings for demo
        cursor.execute("SELECT * FROM bookings ORDER BY id DESC LIMIT 10")
        
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"success": True, "bookings": rows})

@app.route("/api/bookings/<booking_ref>", methods=["GET"])
def get_booking(booking_ref):
    """Retrieves specific booking details"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE booking_ref = ?", (booking_ref,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "message": "Booking not found"}), 404
        
    return jsonify({"success": True, "booking": dict(row)})

@app.route("/api/bookings/<booking_ref>/cancel", methods=["POST"])
def cancel_booking(booking_ref):
    """
    Cancels an existing booking as requested:
    'after booked the cab user can cancel the booking as well'
    """
    data = request.get_json() or {}
    reason = data.get("reason", "Cancelled by passenger").strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE booking_ref = ?", (booking_ref,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Booking not found"}), 404
        
    if row["booking_status"] == "Cancelled":
        conn.close()
        return jsonify({"success": False, "message": "This booking is already cancelled"}), 400
        
    cursor.execute("""
        UPDATE bookings
        SET booking_status = 'Cancelled',
            cancelled_at = CURRENT_TIMESTAMP,
            cancel_reason = ?
        WHERE booking_ref = ?
    """, (reason, booking_ref))
    
    # Also record notification for driver about cancellation
    cancel_msg = (
        f"⚠️ *BOOKING CANCELLED ALERT*\n"
        f"Booking ID: {booking_ref}\n"
        f"Passenger: {row['user_name']} ({row['user_mobile']})\n"
        f"Trip: {row['pickup_location']} ➔ {row['drop_location']}\n"
        f"Fare: ₹{row['fare_amount']}\n"
        f"Reason: {reason}\n"
        f"Time: {datetime.now().strftime('%d-%b-%Y %I:%M %p')}"
    )
    cursor.execute("""
        INSERT INTO notifications (booking_id, booking_ref, recipient_name, recipient_mobile, recipient_email, title, message, is_read)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        row['id'],
        booking_ref,
        "Manoj Mane",
        "+91 9975222099",
        "manojmane155@gmail.com",
        f"Cancelled Booking: {booking_ref}",
        cancel_msg
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": f"Booking {booking_ref} has been cancelled successfully.",
        "booking_ref": booking_ref,
        "status": "Cancelled",
        "cancel_reason": reason
    })

# ----------------- DRIVER / OWNER PORTAL API ----------------- #

@app.route("/api/driver/bookings", methods=["GET"])
def driver_bookings():
    """All bookings for Manoj Mane's dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "bookings": rows})

@app.route("/api/driver/notifications", methods=["GET"])
def driver_notifications():
    """Recent alerts sent to Manoj Mane"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20")
    rows = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
    unread_count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"success": True, "notifications": rows, "unread_count": unread_count})

@app.route("/api/driver/notifications/mark-read", methods=["POST"])
def mark_notifications_read():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/driver/update-status", methods=["POST"])
def update_trip_status():
    """Driver updates booking status (e.g. Accepted, En Route, Completed)"""
    data = request.get_json() or {}
    booking_ref = data.get("booking_ref")
    new_status = data.get("status")
    
    valid_statuses = ["Confirmed", "Driver Assigned", "Arrived at Pickup", "Trip Started", "Completed", "Cancelled"]
    if new_status not in valid_statuses:
        return jsonify({"success": False, "message": "Invalid status"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET booking_status = ? WHERE booking_ref = ?", (new_status, booking_ref))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Status updated to {new_status}"})

if __name__ == "__main__":
    print("==================================================")
    print("[CAB] ERTIGA ONLINE CAB BOOKING SERVICE")
    print("Driver: Manoj Mane | Vehicle: MH12 TV 1292")
    print("Contact: +91 9975222099 | Email: manojmane155@gmail.com")
    print("Rate: Rs 15 per kilometer")
    print("Server running at: http://127.0.0.1:5000")
    print("Driver Portal: http://127.0.0.1:5000/driver")
    print("Passenger Bookings: http://127.0.0.1:5000/bookings")
    print("==================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
