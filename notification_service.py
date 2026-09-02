import urllib.parse
from datetime import datetime
from database import get_db

def format_booking_alert_message(booking_data):
    """
    Formats the notification message with all required booking details:
    - User Name
    - Mobile number
    - Pickup point and destination details
    - Booking date and time
    - Onboard date and time
    - Cab booked total amount
    """
    created_str = booking_data.get('created_at')
    if isinstance(created_str, datetime):
        booking_time_str = created_str.strftime('%d-%b-%Y %I:%M %p')
    elif created_str:
        booking_time_str = str(created_str)
    else:
        booking_time_str = datetime.now().strftime('%d-%b-%Y %I:%M %p')

    message = (
        f"🚖 *NEW CAB BOOKING CONFIRMED!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚘 *Vehicle:* Maruti Suzuki Ertiga ({booking_data.get('car_number', 'MH12 TV 1292')})\n"
        f"👤 *Driver/Owner:* {booking_data.get('driver_name', 'Manoj Mane')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *Booking ID:* {booking_data.get('booking_ref')}\n"
        f"🙋‍♂️ *Passenger Name:* {booking_data.get('user_name')}\n"
        f"📞 *Mobile Number:* {booking_data.get('user_mobile')}\n"
        f"📍 *Pickup Location:* {booking_data.get('pickup_location')}\n"
        f"🏁 *Destination Details:* {booking_data.get('drop_location')}\n"
        f"🕒 *Booking Date & Time:* {booking_time_str}\n"
        f"📅 *Onboard Date & Time:* {booking_data.get('onboard_date')} at {booking_data.get('onboard_time')}\n"
        f"📏 *Estimated Distance:* {booking_data.get('distance_km')} KM\n"
        f"🏷️ *Rate:* ₹{booking_data.get('rate_per_km', 15)} / KM\n"
        f"💰 *Cab Booked Total Amount:* ₹{booking_data.get('fare_amount'):,.2f}\n"
        f"💳 *Payment Mode:* {booking_data.get('payment_method')} ({booking_data.get('payment_status', 'Pending')})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Please be ready at the pickup point on schedule!"
    )
    return message

def send_driver_notification(booking_data):
    """
    Saves notification to DB, prepares WhatsApp link and SMS dispatch record.
    Notifies driver Manoj Mane (+91 9975222099, manojmane155@gmail.com).
    """
    message_text = format_booking_alert_message(booking_data)
    
    driver_mobile = "+91 9975222099"
    driver_email = "manojmane155@gmail.com"
    driver_name = "Manoj Mane"
    
    # Generate WhatsApp URL
    clean_mobile = "919975222099"
    encoded_text = urllib.parse.quote(message_text)
    whatsapp_url = f"https://wa.me/{clean_mobile}?text={encoded_text}"
    
    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (booking_id, booking_ref, recipient_name, recipient_mobile, recipient_email, title, message, is_read)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        booking_data.get('id'),
        booking_data.get('booking_ref'),
        driver_name,
        driver_mobile,
        driver_email,
        f"New Booking: {booking_data.get('booking_ref')} - ₹{booking_data.get('fare_amount')}",
        message_text
    ))
    conn.commit()
    notification_id = cursor.lastrowid
    conn.close()
    
    return {
        "status": "success",
        "notification_id": notification_id,
        "recipient_name": driver_name,
        "recipient_mobile": driver_mobile,
        "recipient_email": driver_email,
        "message": message_text,
        "whatsapp_url": whatsapp_url
    }
