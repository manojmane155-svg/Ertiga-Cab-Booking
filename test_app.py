import unittest
import json
from app import app
from database import init_db, get_db

class TestErtigaCabBooking(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        init_db()

    def test_01_driver_config(self):
        """Verify driver Manoj Mane, Ertiga MH12 TV 1292, phone, email, and rate 15"""
        response = self.client.get('/api/driver-info')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        driver = data['driver']
        self.assertEqual(driver['name'], 'Manoj Mane')
        self.assertEqual(driver['car_model'], 'Maruti Suzuki Ertiga')
        self.assertEqual(driver['car_number'], 'MH12 TV 1292')
        self.assertEqual(driver['mobile'], '+91 9975222099')
        self.assertEqual(driver['email'], 'manojmane155@gmail.com')
        self.assertEqual(driver['per_km_rate'], 15.0)

    def test_02_otp_auth_flow(self):
        """Verify mobile OTP login flow"""
        # Step 1: Send OTP
        send_res = self.client.post('/api/auth/send-otp', json={
            'mobile': '9975222099',
            'name': 'Manoj Test User'
        })
        self.assertEqual(send_res.status_code, 200)
        send_data = json.loads(send_res.data)
        self.assertTrue(send_data['success'])
        otp = send_data['otp']
        self.assertEqual(len(otp), 6)

        # Step 2: Verify OTP
        verify_res = self.client.post('/api/auth/verify-otp', json={
            'mobile': '9975222099',
            'otp': otp,
            'name': 'Manoj Test User'
        })
        self.assertEqual(verify_res.status_code, 200)
        verify_data = json.loads(verify_res.data)
        self.assertTrue(verify_data['success'])
        self.assertEqual(verify_data['user']['name'], 'Manoj Test User')

    def test_03_fare_calculation_at_15_per_km(self):
        """Verify fare is strictly calculated as distance_km * 15.0"""
        res = self.client.post('/api/calculate-fare', json={
            'pickup': 'Pune Railway Station',
            'drop': 'Pune Airport (PNQ), Lohegaon',
            'distance_km': 20.0
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['rate_per_km'], 15.0)
        self.assertEqual(data['distance_km'], 20.0)
        # 20 km * 15 Rs = 300 Rs
        self.assertEqual(data['total_amount'], 300.0)

    def _create_sample_booking(self):
        booking_payload = {
            'user_name': 'Rahul Sharma',
            'user_mobile': '9876543210',
            'pickup_location': 'Shivaji Nagar, Pune',
            'drop_location': 'Hinjewadi Phase 1, IT Park',
            'distance_km': 16.0,
            'onboard_date': '2026-09-05',
            'onboard_time': '08:30 AM - 09:30 AM',
            'payment_method': 'UPI'
        }
        res = self.client.post('/api/bookings', json=booking_payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        return data

    def test_04_create_booking_and_notification(self):
        """Verify booking creation and driver notification payload"""
        data = self._create_sample_booking()
        self.assertTrue(data['success'])
        
        booking = data['booking']
        self.assertEqual(booking['user_name'], 'Rahul Sharma')
        self.assertEqual(booking['rate_per_km'], 15.0)
        # 16 km * 15 = 240
        self.assertEqual(booking['fare_amount'], 240.0)
        self.assertEqual(booking['booking_status'], 'Confirmed')
        
        # Check driver notification
        notif = data['notification']
        self.assertEqual(notif['recipient_name'], 'Manoj Mane')
        self.assertEqual(notif['recipient_mobile'], '+91 9975222099')
        self.assertEqual(notif['recipient_email'], 'manojmane155@gmail.com')
        # Check message body includes all required items
        msg = notif['message']
        self.assertIn('Rahul Sharma', msg)
        self.assertIn('9876543210', msg)
        self.assertIn('Shivaji Nagar, Pune', msg)
        self.assertIn('Hinjewadi Phase 1, IT Park', msg)
        self.assertIn('2026-09-05', msg)
        self.assertIn('₹240.00', msg)

    def test_05_cancel_booking(self):
        """Verify booking cancellation as required by prompt"""
        data = self._create_sample_booking()
        ref = data['booking']['booking_ref']
        
        cancel_res = self.client.post(f'/api/bookings/{ref}/cancel', json={
            'reason': 'Customer requested trip cancellation due to rain'
        })
        self.assertEqual(cancel_res.status_code, 200)
        cancel_data = json.loads(cancel_res.data)
        self.assertTrue(cancel_data['success'])
        self.assertEqual(cancel_data['status'], 'Cancelled')

        # Check booking status in GET
        get_res = self.client.get(f'/api/bookings/{ref}')
        get_data = json.loads(get_res.data)
        self.assertEqual(get_data['booking']['booking_status'], 'Cancelled')
        self.assertEqual(get_data['booking']['cancel_reason'], 'Customer requested trip cancellation due to rain')

    def test_06_driver_dashboard_apis(self):
        """Verify driver bookings and notifications retrieval"""
        b_res = self.client.get('/api/driver/bookings')
        self.assertEqual(b_res.status_code, 200)
        b_data = json.loads(b_res.data)
        self.assertTrue(b_data['success'])
        self.assertIsInstance(b_data['bookings'], list)

        n_res = self.client.get('/api/driver/notifications')
        self.assertEqual(n_res.status_code, 200)
        n_data = json.loads(n_res.data)
        self.assertTrue(n_data['success'])
        self.assertIsInstance(n_data['notifications'], list)

if __name__ == '__main__':
    unittest.main()
