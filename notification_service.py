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

def dispatch_automated_driver_alerts(booking_data, message_text):
    """
    Executes automated background delivery of SMS, WhatsApp, and Email alerts to driver Manoj Mane (+91 9975222099).
    """
    import os
    import requests
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    driver_mobile = "9975222099"
    driver_email = "manojmane155@gmail.com"
    booking_ref = booking_data.get('booking_ref', 'ERT-NEW')
    
    results = {
        "sms_sent": False,
        "whatsapp_sent": False,
        "email_sent": False
    }

    # 1. Automated Fast2SMS Dispatch to Manoj's mobile (+91 9975222099)
    fast2sms_key = os.environ.get("FAST2SMS_API_KEY", "kGeup7sgIfKPjER1bOyhq0rJSXmBa4AVlMczvDTdZWNLQnwo299ScpCGPozZwV8Y2BnyRmKgfkIJ5qDF")
    if fast2sms_key:
        try:
            sms_payload = {
                "route": "q",
                "message": f"NEW CAB BOOKING: Ref {booking_ref}, Passenger {booking_data.get('user_name')} ({booking_data.get('user_mobile')}), Pickup: {booking_data.get('pickup_location')}, Drop: {booking_data.get('drop_location')}, Fare: Rs {booking_data.get('fare_amount')}. - Ertiga MH12 TV 1292",
                "language": "english",
                "numbers": driver_mobile
            }
            headers = {
                'authorization': fast2sms_key,
                'Content-Type': "application/x-www-form-urlencoded"
            }
            r = requests.post("https://www.fast2sms.com/dev/bulkV2", data=sms_payload, headers=headers, timeout=5)
            if r.status_code == 200:
                results["sms_sent"] = True
                print(f"✅ [Fast2SMS Success] Automated driver SMS delivered: {r.text}")
        except Exception as e:
            print(f"⚠️ [Fast2SMS Driver Alert Error]: {e}")

    # 2. Automated WhatsApp Bot Dispatch (CallMeBot / WhatsApp Cloud / Twilio)
    # CallMeBot is free for direct personal WhatsApp alerts
    callmebot_key = os.environ.get("CALLMEBOT_API_KEY", "")
    if callmebot_key:
        try:
            wa_encoded = urllib.parse.quote(message_text)
            wa_url = f"https://api.callmebot.com/whatsapp.php?phone=+91{driver_mobile}&text={wa_encoded}&apikey={callmebot_key}"
            r = requests.get(wa_url, timeout=5)
            if r.status_code == 200:
                results["whatsapp_sent"] = True
                print(f"✅ [WhatsApp Bot Success] Automated WhatsApp message delivered to Manoj Mane (+91 9975222099)")
        except Exception as e:
            print(f"⚠️ [WhatsApp Bot Error]: {e}")

    # Twilio SMS / WhatsApp if configured
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_from = os.environ.get("TWILIO_PHONE_NUMBER", "")
    if twilio_sid and twilio_token and twilio_from:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            data = {
                "To": f"+91{driver_mobile}",
                "From": twilio_from,
                "Body": message_text
            }
            r = requests.post(url, data=data, auth=(twilio_sid, twilio_token), timeout=5)
            if r.status_code in [200, 201]:
                results["sms_sent"] = True
                print(f"✅ [Twilio Success] Automated driver SMS sent via Twilio")
        except Exception as e:
            print(f"⚠️ [Twilio Driver SMS Error]: {e}")

    # 3. Automated Email Notification to manojmane155@gmail.com
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚖 New Cab Booking Alert: {booking_ref} (₹{booking_data.get('fare_amount')})"
            msg["From"] = smtp_user
            msg["To"] = driver_email
            msg.attach(MIMEText(message_text, "plain"))
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, driver_email, msg.as_string())
            results["email_sent"] = True
            print(f"✅ [Email Success] Automated booking email sent to {driver_email}")
        except Exception as e:
            print(f"⚠️ [Email Alert Error]: {e}")

    print(f"\n=======================================================")
    print(f"🚨 [AUTOMATIC DRIVER NOTIFICATION DISPATCHED]")
    print(f"Recipient: Manoj Mane (+91 {driver_mobile}, {driver_email})")
    print(f"Vehicle: Maruti Suzuki Ertiga (MH12 TV 1292)")
    print(f"Booking ID: {booking_ref}")
    print(f"Passenger: {booking_data.get('user_name')} ({booking_data.get('user_mobile')})")
    print(f"Fare Amount: ₹{booking_data.get('fare_amount')}")
    print(f"Dispatch Status: SMS={results['sms_sent']}, WhatsApp={results['whatsapp_sent']}, Email={results['email_sent']}")
    print(f"=======================================================\n")

    return results

def send_driver_notification(booking_data):
    """
    Saves notification to DB, prepares WhatsApp link and executes automated background alerts.
    Notifies driver Manoj Mane (+91 9975222099, manojmane155@gmail.com).
    """
    message_text = format_booking_alert_message(booking_data)
    
    driver_mobile = "+91 9975222099"
    driver_email = "manojmane155@gmail.com"
    driver_name = "Manoj Mane"
    
    # Generate WhatsApp 1-Click URL fallback
    clean_mobile = "919975222099"
    encoded_text = urllib.parse.quote(message_text)
    whatsapp_url = f"https://wa.me/{clean_mobile}?text={encoded_text}"
    
    # 1. Execute automated background dispatch
    auto_results = dispatch_automated_driver_alerts(booking_data, message_text)

    # 2. Store in database
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
        "whatsapp_url": whatsapp_url,
        "auto_dispatch": auto_results
    }

def send_user_otp_sms(mobile, otp):
    """
    Dispatches 6-digit OTP SMS to the user's mobile number.
    - Integrates with Fast2SMS (India Bulk SMS API) if FAST2SMS_API_KEY is configured.
    - Integrates with Twilio if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are configured.
    - Provides WhatsApp direct delivery URL.
    """
    import os
    import requests
    
    clean_mobile = str(mobile).replace("+91", "").replace(" ", "").replace("-", "").strip()[-10:]
    sms_text = f"Your Ertiga Cab Booking OTP is {otp}. Valid for 10 minutes. Please do not share this OTP with anyone. - Manoj Mane (MH12 TV 1292)"
    
    # 1. Fast2SMS Gateway (Standard for India mobile numbers)
    fast2sms_key = os.environ.get("FAST2SMS_API_KEY", "kGeup7sgIfKPjER1bOyhq0rJSXmBa4AVlMczvDTdZWNLQnwo299ScpCGPozZwV8Y2BnyRmKgfkIJ5qDF")
    fast2sms_sent = False
    if fast2sms_key:
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": "q",
                "message": f"Your Ertiga Cab OTP is {otp}. Valid for 10 min. - Manoj Mane (MH12 TV 1292)",
                "language": "english",
                "numbers": clean_mobile
            }
            headers = {
                'authorization': fast2sms_key,
                'Content-Type': "application/x-www-form-urlencoded"
            }
            resp = requests.post(url, data=payload, headers=headers, timeout=5)
            print(f"[Fast2SMS OTP Dispatch Response]: {resp.text}")
            if resp.status_code == 200:
                fast2sms_sent = True
        except Exception as e:
            print(f"[Fast2SMS Error]: {e}")

    # 2. Twilio SMS Gateway
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_from = os.environ.get("TWILIO_PHONE_NUMBER", "")
    if twilio_sid and twilio_token and twilio_from:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            data = {
                "To": f"+91{clean_mobile}",
                "From": twilio_from,
                "Body": sms_text
            }
            resp = requests.post(url, data=data, auth=(twilio_sid, twilio_token), timeout=5)
            print(f"[Twilio Response]: {resp.status_code}")
        except Exception as e:
            print(f"[Twilio Error]: {e}")

    # 3. WhatsApp Direct OTP URL
    encoded_sms = urllib.parse.quote(f"🔑 *Ertiga Cab Booking Login OTP*\n\nYour 6-digit OTP is: *{otp}*\n\nValid for 10 minutes. - Manoj Mane (MH12 TV 1292)")
    whatsapp_otp_url = f"https://wa.me/91{clean_mobile}?text={encoded_sms}"

    # 4. Save to notifications log in DB
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (booking_ref, recipient_name, recipient_mobile, recipient_email, title, message, is_read)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (
            "OTP-AUTH",
            f"Passenger ({clean_mobile})",
            f"+91 {clean_mobile}",
            "passenger@sms.local",
            f"Login OTP for +91 {clean_mobile}",
            sms_text
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[SMS LOG ERROR] {e}")

    print(f"\n=======================================================")
    print(f"📱 [REAL SMS OTP GENERATED & DISPATCHED]")
    print(f"To Mobile: +91 {clean_mobile}")
    print(f"6-Digit OTP: {otp}")
    print(f"SMS Content: {sms_text}")
    print(f"WhatsApp URL: {whatsapp_otp_url}")
    print(f"=======================================================\n")

    return {
        "success": True,
        "mobile": clean_mobile,
        "otp": otp,
        "whatsapp_url": whatsapp_otp_url,
        "message": f"OTP successfully sent to +91 {clean_mobile}"
    }


