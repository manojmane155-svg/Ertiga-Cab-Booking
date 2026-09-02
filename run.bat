@echo off
title Ertiga Cab Booking Service - Manoj Mane (MH12 TV 1292)
echo ===================================================
echo   🚖 ERTIGA ONLINE CAB BOOKING WEBSITE
echo   Vehicle: Maruti Suzuki Ertiga (MH12 TV 1292)
echo   Owner / Driver: Manoj Mane
echo   Contact: +91 9975222099 | manojmane155@gmail.com
echo   Fare Rate: Rs. 15 per Kilometer
echo ===================================================
echo.
echo Starting Web Server on http://localhost:5000 ...
echo.

start "" http://localhost:5000
python app.py

pause
