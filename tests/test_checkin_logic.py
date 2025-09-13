"""
Unit tests for check-in logic implementation
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, AttendanceStatus, get_attendance_status
from models import Employee
from database import DatabaseQueryError


class TestAttendanceStatus(unittest.TestCase):
    """Test cases for AttendanceStatus enumeration"""
    
    def test_attendance_status_constants(self):
        """Test that AttendanceStatus constants are defined correctly"""
        self.assertEqual(AttendanceStatus.NOT_CHECKED_IN, "not_checked_in")
        self.assertEqual(AttendanceStatus.CHECKED_IN, "checked_in")
        self.assertEqual(AttendanceStatus.COMPLETED, "completed")


class TestGetAttendanceStatus(unittest.TestCase):
    """Test cases for get_attendance_status function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.employee_id = 1
        
        # Sample attendance records
        self.no_attendance = None
        self.checked_in_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 9, 0, 0),
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 9, 0, 0)
        }
        self.completed_attendance = {
            'id': 2,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 9, 0, 0),
            'check_out_time': datetime(2024, 1, 15, 17, 30, 0),
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 9, 0, 0)
        }
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_not_checked_in(self, mock_attendance_repo):
        """Test get_attendance_status when employee hasn't checked in"""
        # Arrange
        mock_attendance_repo.get_today_attendance.return_value = None
        
        # Act
        result = get_attendance_status(self.employee_id)
        
        # Assert
        self.assertEqual(result, AttendanceStatus.NOT_CHECKED_IN)
        mock_attendance_repo.get_today_attendance.assert_called_once_with(self.employee_id)
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_checked_in(self, mock_attendance_repo):
        """Test get_attendance_status when employee is checked in but not out"""
        # Arrange
        mock_attendance_repo.get_today_attendance.return_value = self.checked_in_attendance
        
        # Act
        result = get_attendance_status(self.employee_id)
        
        # Assert
        self.assertEqual(result, AttendanceStatus.CHECKED_IN)
        mock_attendance_repo.get_today_attendance.assert_called_once_with(self.employee_id)
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_completed(self, mock_attendance_repo):
        """Test get_attendance_status when employee has completed attendance"""
        # Arrange
        mock_attendance_repo.get_today_attendance.return_value = self.completed_attendance
        
        # Act
        result = get_attendance_status(self.employee_id)
        
        # Assert
        self.assertEqual(result, AttendanceStatus.COMPLETED)
        mock_attendance_repo.get_today_attendance.assert_called_once_with(self.employee_id)
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_database_error(self, mock_attendance_repo):
        """Test get_attendance_status when database error occurs"""
        # Arrange
        mock_attendance_repo.get_today_attendance.side_effect = DatabaseQueryError("Database connection failed")
        
        # Act
        result = get_attendance_status(self.employee_id)
        
        # Assert
        # Should return NOT_CHECKED_IN as default on error
        self.assertEqual(result, AttendanceStatus.NOT_CHECKED_IN)


class TestCheckInRoute(unittest.TestCase):
    """Test cases for /check-in POST route"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Sample employee for testing
        self.test_employee = Employee(
            id=1,
            google_id='google_123456789',
            email='test@company.com',
            name='Test Employee'
        )
        
        # Sample attendance record
        self.sample_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 9, 0, 0),
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 9, 0, 0)
        }
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_success(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test successful check-in operation"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        mock_attendance_repo.create_checkin.return_value = self.sample_attendance
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        self.assertIn('Check-in successful', response_data['message'])
        self.assertIn('check_in_time', response_data)
        self.assertIn('attendance_id', response_data)
        
        # Verify repository was called
        mock_attendance_repo.create_checkin.assert_called_once_with(1)
    
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_already_checked_in(self, mock_get_user, mock_get_status):
        """Test check-in when employee is already checked in"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('already checked in today', response_data['error'])
    
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_already_completed(self, mock_get_user, mock_get_status):
        """Test check-in when employee has already completed attendance"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.COMPLETED
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('already completed attendance', response_data['error'])
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_duplicate_prevention(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test duplicate check-in prevention at repository level"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        mock_attendance_repo.create_checkin.side_effect = DatabaseQueryError("Employee 1 has already checked in today")
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('already checked in today', response_data['error'])
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_database_error(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test check-in with general database error"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        mock_attendance_repo.create_checkin.side_effect = DatabaseQueryError("Database connection failed")
        
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
    def test_check_in_unexpected_error(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test check-in with unexpected error"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        mock_attendance_repo.create_checkin.side_effect = Exception("Unexpected error")
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 500)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('Check-in failed', response_data['error'])
    
    def test_check_in_unauthenticated(self):
        """Test check-in route requires authentication"""
        # Act
        response = self.client.post('/check-in')
        
        # Assert
        # Should redirect to login page (302) or return 401
        self.assertIn(response.status_code, [302, 401])
    
    def test_check_in_wrong_method(self):
        """Test check-in route only accepts POST method"""
        # Act
        response = self.client.get('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_time_formatting(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test that check-in time is properly formatted in response"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        # Test with specific time
        test_time = datetime(2024, 1, 15, 14, 30, 0)  # 2:30 PM
        attendance_with_time = self.sample_attendance.copy()
        attendance_with_time['check_in_time'] = test_time
        mock_attendance_repo.create_checkin.return_value = attendance_with_time
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Check time formatting (should be in 12-hour format with AM/PM)
        formatted_time = response_data['check_in_time']
        self.assertEqual(formatted_time, '02:30 PM')
    
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    @patch('flask_login.utils._get_user')
    def test_check_in_string_time_handling(self, mock_get_user, mock_get_status, mock_attendance_repo):
        """Test check-in handles string time values gracefully"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        # Test with string time (edge case)
        attendance_with_string_time = self.sample_attendance.copy()
        attendance_with_string_time['check_in_time'] = "2024-01-15 09:00:00"
        mock_attendance_repo.create_checkin.return_value = attendance_with_string_time
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Should handle string time gracefully
        self.assertIn('check_in_time', response_data)
        self.assertEqual(response_data['check_in_time'], "2024-01-15 09:00:00")


if __name__ == '__main__':
    unittest.main()