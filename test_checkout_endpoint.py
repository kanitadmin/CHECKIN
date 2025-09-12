"""
Functional tests for check-out HTTP endpoint
Tests the /check-out POST route functionality
"""
import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime
from app import app, AttendanceStatus
from models import Employee


class TestCheckoutEndpoint(unittest.TestCase):
    """Test check-out HTTP endpoint functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a test user
        self.test_user = Employee(
            id=1,
            google_id='test_google_id',
            email='test@company.com',
            name='Test User'
        )
    
    def test_checkout_requires_authentication(self):
        """Test that check-out endpoint requires authentication"""
        response = self.client.post('/check-out')
        
        # Should redirect to login or return 401
        self.assertIn(response.status_code, [302, 401])
    
    @patch('app.current_user')
    @patch('app.get_attendance_status')
    @patch('app.attendance_repo.update_checkout')
    def test_checkout_success_response_format(self, mock_update_checkout, mock_get_status, mock_current_user):
        """Test check-out success response format"""
        # Mock authentication
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        # Mock status and repository response
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        mock_update_checkout.return_value = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': datetime(2023, 12, 1, 17, 0, 0),
            'work_date': '2023-12-01'
        }
        
        # Bypass login_required decorator for this test
        with patch('flask_login.login_required', lambda f: f):
            response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Check-out successful!', data['message'])
        self.assertIn('check_in_time', data)
        self.assertIn('check_out_time', data)
        self.assertIn('attendance_id', data)
    
    @patch('app.current_user')
    @patch('app.get_attendance_status')
    def test_checkout_validation_errors(self, mock_get_status, mock_current_user):
        """Test check-out validation error responses"""
        # Mock authentication
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        
        # Test not checked in error
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        with patch('flask_login.login_required', lambda f: f):
            response = self.client.post('/check-out')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'You must check in first before checking out.')
        
        # Test already completed error
        mock_get_status.return_value = AttendanceStatus.COMPLETED
        
        with patch('flask_login.login_required', lambda f: f):
            response = self.client.post('/check-out')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'You have already completed attendance for today.')


class TestCheckoutErrorHandling(unittest.TestCase):
    """Test check-out error handling scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('app.current_user')
    @patch('app.get_attendance_status')
    @patch('app.attendance_repo.update_checkout')
    def test_checkout_repository_error_handling(self, mock_update_checkout, mock_get_status, mock_current_user):
        """Test check-out handles repository errors correctly"""
        # Mock authentication
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        
        # Test specific error cases
        test_cases = [
            ("Employee 1 has not checked in today", 400, "You must check in first before checking out."),
            ("Employee 1 has already checked out today", 400, "You have already checked out for today."),
            ("Database connection failed", 500, "Check-out failed. Please try again.")
        ]
        
        for error_message, expected_status, expected_error in test_cases:
            with self.subTest(error=error_message):
                mock_update_checkout.side_effect = Exception(error_message)
                
                with patch('flask_login.login_required', lambda f: f):
                    response = self.client.post('/check-out')
                
                self.assertEqual(response.status_code, expected_status)
                data = json.loads(response.data)
                self.assertFalse(data['success'])
                self.assertEqual(data['error'], expected_error)


if __name__ == '__main__':
    unittest.main()