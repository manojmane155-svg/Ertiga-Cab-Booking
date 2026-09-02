# 🚖 Maruti Suzuki Ertiga Online Cab Booking Platform

A modern, responsive, Ola/Uber-style cab booking web platform customized for **Manoj Mane's Maruti Suzuki Ertiga (MH12 TV 1292)**.

---

## 📋 Vehicle & Driver Information
- **Vehicle**: Maruti Suzuki Ertiga (6+1 Seater, White, AC Climate Control, Large Boot Space)
- **Registration Number**: `MH12 TV 1292`
- **Owner & Driver Name**: `Manoj Mane`
- **Driver Mobile Number**: `+91 9975222099`
- **Driver Email**: `manojmane155@gmail.com`
- **Fare Rate**: **₹15 per kilometer** (`Total Fare = Distance in km × ₹15`)

---

## 🌟 Key Features

1. **User Authentication via Mobile Number & OTP**:
   - Any passenger can log in using their 10-digit mobile number.
   - Fast 6-digit OTP verification with 1-click auto-fill option for frictionless testing.
2. **Real-time Cab Availability**:
   - Live availability badge showing whether Manoj Mane's Ertiga is online and ready for hire.
   - Driver rating (4.9★), features (AC, 6+1 seats, sanitized, music system).
3. **Interactive Route & Source/Destination Selection**:
   - Select Source (Pickup) and Destination (Drop) from popular landmarks or custom addresses.
   - Interactive Leaflet & OpenStreetMap route polyline display.
4. **Transparent Distance & ₹15/km Rent Calculation**:
   - Automatic road-distance estimation between pickup and destination.
   - Displays clear breakdown: Distance (km), Rate (₹15/km), Estimated duration, and Total Amount.
5. **Pickup Date & Time Slot Scheduler**:
   - Onboard date picker (prevents past dates).
   - Convenient time slot dropdowns (Early Morning, Morning Peak, Afternoon, Evening Peak, Night).
6. **Multi-Option Payment Gateway**:
   - UPI (GPay, PhonePe, Paytm, QR scan)
   - Debit Card (Visa, RuPay, MasterCard)
   - Credit Card
   - Cash on Delivery (COD / Pay in Cab)
7. **Ride Cancellation**:
   - Passengers can cancel their active booking anytime from the "My Rides" section with a reason.
8. **Instant Driver & Owner Notification**:
   - Automated notification dispatched immediately upon booking to **Manoj Mane (+91 9975222099, manojmane155@gmail.com)** containing:
     - Passenger Full Name
     - Mobile Number
     - Pickup Location & Destination Details
     - Booking Date and Time
     - Onboard Date and Time Slot
     - Total Cab Booked Amount
     - Payment Method
   - Includes **1-Click WhatsApp Chat** link pre-filled with the booking alert.
   - Live **Driver Console** (`/driver`) with incoming sound chime and visual alert banners.

---

## 🚀 How to Run the Website

### Option 1: Double-Click Startup
Double click `run.bat` in the project directory.

### Option 2: Command Line
```powershell
cd C:\Users\MANOJ\.gemini\antigravity\scratch\ertiga_cab_booking
python app.py
```

Open your browser at:
- **Passenger Booking Portal**: [http://localhost:5000](http://localhost:5000)
- **My Rides & Cancellation**: [http://localhost:5000/bookings](http://localhost:5000/bookings)
- **Driver & Owner Dashboard**: [http://localhost:5000/driver](http://localhost:5000/driver)

---

## 🧪 Testing
Run the automated test suite:
```powershell
python test_app.py
```
