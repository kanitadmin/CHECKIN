"""
Unit tests for check-out logic implementation
Tests the /check-out POST route validation and business logic
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from app import app, AttendanceStatus, get_attendance_status
from models import Employee


class TestCheckoutLogic(unittest.TestCase):
    """Test cases for check-out logic and validation"""
    
    def setUp(self):
        """Set up test client and mock data"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Mock employee data
        self.mock_employee = Employee(
            id=1,
            google_id='test_google_id',
            email='test@company.com',
            name='Test User',
            picture_url='http://example.com/pic.jpg'
        )
        
        # Mock attendance record
        self.mock_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': None,
            'work_date': '2023-12-01',
            'created_at': datetime(2023, 12, 1, 9, 0, 0)
        }
        
        self.mock_completed_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': datetime(2023, 12, 1, 17, 0, 0),
            'work_date': '2023-12-01',
            'created_at': datetime(2023, 12, 1, 9, 0, 0)
        }
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    def test_successful_checkout(self, mock_get_status, mock_attendance_repo, mock_current_user):
        """Test successful check-out when user is checked in"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        
        updated_attendance = self.mock_attendance.copy()
        updated_attendance['check_out_time'] = datetime(2023, 12, 1, 17, 0, 0)
        mock_attendance_repo.update_checkout.return_value = updated_attendance
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Check-out successful!', data['message'])
        self.assertEqual(data['check_in_time'], '09:00 AM')
        self.assertEqual(data['check_out_time'], '05:00 PM')
        self.assertEqual(data['attendance_id'], 1)
        
        # Verify repository method was called
        mock_attendance_repo.update_checkout.assert_called_once_with(1)
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.get_attendance_status')
    def test_checkout_without_checkin(self, mock_get_status, mock_current_user):
        """Test check-out fails when user hasn't checked in"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        
        mock_get_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'You must check in first before checking out.')
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.get_attendance_status')
    def test_checkout_already_completed(self, mock_get_status, mock_current_user):
        """Test check-out fails when attendance is already completed"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        
        mock_get_status.return_value = AttendanceStatus.COMPLETED
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'You have already completed attendance for today.')
    
    def test_checkout_requires_authentication(self):
        """Test check-out route requires authentication"""
        response = self.client.post('/check-out')
        
        # Should redirect to login (302) or return 401
        self.assertIn(response.status_code, [302, 401])
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    def test_checkout_repository_error_not_checked_in(self, mock_get_status, mock_attendance_repo, mock_current_user):
        """Test check-out handles repository error for not checked in"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        mock_attendance_repo.update_checkout.side_effect = Exception("Employee 1 has not checked in today")
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'You must check in first before checking out.')
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    def test_checkout_repository_error_already_checked_out(self, mock_get_status, mock_attendance_repo, mock_current_user):
        """Test check-out handles repository error for already checked out"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        mock_attendance_repo.update_checkout.side_effect = Exception("Employee 1 has already checked out today")
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'You have already checked out for today.')
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    def test_checkout_generic_error(self, mock_get_status, mock_attendance_repo, mock_current_user):
        """Test check-out handles generic repository errors"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        mock_attendance_repo.update_checkout.side_effect = Exception("Database connection failed")
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Check-out failed. Please try again.')
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    def test_checkout_time_formatting(self, mock_get_status, mock_attendance_repo, mock_current_user):
        """Test check-out properly formats check-in and check-out times"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        
        # Test with different time formats
        updated_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 8, 30, 0),  # 8:30 AM
            'check_out_time': datetime(2023, 12, 1, 16, 45, 0),  # 4:45 PM
            'work_date': '2023-12-01',
            'created_at': datetime(2023, 12, 1, 8, 30, 0)
        }
        mock_attendance_repo.update_checkout.return_value = updated_attendance
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['check_in_time'], '08:30 AM')
        self.assertEqual(data['check_out_time'], '04:45 PM')
    
    @patch('app.login_required', lambda f: f)  # Bypass login_required decorator
    @patch('app.current_user')
    @patch('app.attendance_repo')
    @patch('app.get_attendance_status')
    def test_checkout_with_string_times(self, mock_get_status, mock_attendance_repo, mock_current_user):
        """Test check-out handles string time values gracefully"""
        # Setup mocks
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        mock_current_user.email = 'test@company.com'
        
        mock_get_status.return_value = AttendanceStatus.CHECKED_IN
        
        # Test with string time values (edge case)
        updated_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': '2023-12-01 09:00:00',
            'check_out_time': '2023-12-01 17:00:00',
            'work_date': '2023-12-01',
            'created_at': '2023-12-01 09:00:00'
        }
        mock_attendance_repo.update_checkout.return_value = updated_attendance
        
        # Make request
        response = self.client.post('/check-out')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        # Should handle string times gracefully
        self.assertEqual(data['check_in_time'], '2023-12-01 09:00:00')
        self.assertEqual(data['check_out_time'], '2023-12-01 17:00:00')


class TestCheckoutValidation(unittest.TestCase):
    """Test cases for check-out validation logic"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_checked_in(self, mock_attendance_repo):
        """Test attendance status detection for checked in state"""
        mock_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': None,
            'work_date': '2023-12-01'
        }
        mock_attendance_repo.get_today_attendance.return_value = mock_attendance
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.CHECKED_IN)
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_completed(self, mock_attendance_repo):
        """Test attendance status detection for completed state"""
        mock_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': datetime(2023, 12, 1, 17, 0, 0),
            'work_date': '2023-12-01'
        }
        mock_attendance_repo.get_today_attendance.return_value = mock_attendance
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.COMPLETED)
    
    @patch('app.attendance_repo')
    def test_get_attendance_status_not_checked_in(self, mock_attendance_repo):
        """Test attendance status detection for not checked in state"""
        mock_attendance_repo.get_today_attendance.return_value = None
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)


if __name__ == '__main__':
    unittest.main()