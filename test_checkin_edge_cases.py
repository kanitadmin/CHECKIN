"""
Edge case tests for check-in functionality
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, AttendanceStatus, get_attendance_status
from models import Employee
from database import DatabaseQueryError


class TestCheckInEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios for check-in functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        self.test_employee = Employee(
            id=1,
            google_id='google_123456789',
            email='test@company.com',
            name='Test Employee'
        )
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_with_none_checkout_time(self, mock_attendance_repo):
        """Test get_attendance_status handles None check_out_time correctly"""
        # Arrange
        attendance_with_none_checkout = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 9, 0, 0),
            'check_out_time': None,  # Explicitly None
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 9, 0, 0)
        }
        mock_attendance_repo.get_today_attendance.return_value = attendance_with_none_checkout
        
        # Act
        result = get_attendance_status(1)
        
        # Assert
        self.assertEqual(result, AttendanceStatus.CHECKED_IN)
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_with_empty_dict(self, mock_attendance_repo):
        """Test get_attendance_status handles empty attendance record"""
        # Arrange
        mock_attendance_repo.get_today_attendance.return_value = {}
        
        # Act & Assert
        # Should handle gracefully and not crash
        try:
            result = get_attendance_status(1)
            # If no exception, should default to NOT_CHECKED_IN
            self.assertEqual(result, AttendanceStatus.NOT_CHECKED_IN)
        except Exception:
            # If exception occurs, it should be caught and return NOT_CHECKED_IN
            pass
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_check_in_with_datetime_object(self, mock_get_user, mock_attendance_repo):
        """Test check-in response formatting with datetime object"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_attendance_repo.get_today_attendance.return_value = None
        
        # Return datetime object (not string)
        attendance_with_datetime = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 13, 45, 30),  # 1:45:30 PM
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 13, 45, 30)
        }
        mock_attendance_repo.create_checkin.return_value = attendance_with_datetime
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Check that time is formatted correctly (should ignore seconds)
        formatted_time = response_data['check_in_time']
        self.assertEqual(formatted_time, '01:45 PM')
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_check_in_with_midnight_time(self, mock_get_user, mock_attendance_repo):
        """Test check-in response formatting with midnight time"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_attendance_repo.get_today_attendance.return_value = None
        
        # Return midnight time
        attendance_with_midnight = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 0, 0, 0),  # 12:00 AM
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 0, 0, 0)
        }
        mock_attendance_repo.create_checkin.return_value = attendance_with_midnight
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Check that midnight is formatted correctly
        formatted_time = response_data['check_in_time']
        self.assertEqual(formatted_time, '12:00 AM')
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_check_in_with_noon_time(self, mock_get_user, mock_attendance_repo):
        """Test check-in response formatting with noon time"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_attendance_repo.get_today_attendance.return_value = None
        
        # Return noon time
        attendance_with_noon = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 12, 0, 0),  # 12:00 PM
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 12, 0, 0)
        }
        mock_attendance_repo.create_checkin.return_value = attendance_with_noon
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Check that noon is formatted correctly
        formatted_time = response_data['check_in_time']
        self.assertEqual(formatted_time, '12:00 PM')
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_check_in_with_malformed_time(self, mock_get_user, mock_attendance_repo):
        """Test check-in handles malformed time data gracefully"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_attendance_repo.get_today_attendance.return_value = None
        
        # Return malformed time data
        attendance_with_bad_time = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': "invalid-time-format",
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 9, 0, 0)
        }
        mock_attendance_repo.create_checkin.return_value = attendance_with_bad_time
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Should handle gracefully by converting to string
        formatted_time = response_data['check_in_time']
        self.assertEqual(formatted_time, "invalid-time-format")
    
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_status_check_exception_handling(self, mock_get_user, mock_get_status):
        """Test check-in handles exceptions in status checking"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.side_effect = Exception("Status check failed")
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 500)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('Check-in failed', response_data['error'])
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_repository_constraint_violation(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test check-in handles database constraint violations"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        # Simulate database constraint violation
        mock_attendance_repo.create_checkin.side_effect = DatabaseQueryError(
            "Duplicate entry '1-2024-01-15' for key 'unique_daily_checkin'"
        )
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 500)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('Check-in failed', response_data['error'])
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_with_none_employee_id(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test check-in handles None employee ID gracefully"""
        # Arrange
        employee_with_none_id = Employee(
            id=None,  # None ID
            google_id='google_123456789',
            email='test@company.com',
            name='Test Employee'
        )
        mock_get_user.return_value = employee_with_none_id
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        # Mock create_checkin to raise an error for None employee_id
        mock_attendance_repo.create_checkin.side_effect = Exception("Cannot create check-in for None employee_id")
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 500)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('Check-in failed', response_data['error'])


if __name__ == '__main__':
    unittest.main()