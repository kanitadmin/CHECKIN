"""
Integration tests for check-in functionality
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, AttendanceStatus
from models import Employee


class TestCheckInIntegration(unittest.TestCase):
    """Integration tests for check-in functionality"""
    
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
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_complete_checkin_workflow(self, mock_get_user, mock_attendance_repo):
        """Test complete check-in workflow from status check to successful check-in"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        
        # Mock attendance repository responses
        mock_attendance_repo.get_today_attendance.side_effect = [
            None,  # First call: no attendance record (NOT_CHECKED_IN)
            {      # Second call: after check-in creation
                'id': 1,
                'employee_id': 1,
                'check_in_time': '2024-01-15 09:00:00',
                'check_out_time': None,
                'work_date': '2024-01-15',
                'created_at': '2024-01-15 09:00:00'
            }
        ]
        
        mock_attendance_repo.create_checkin.return_value = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': '2024-01-15 09:00:00',
            'check_out_time': None,
            'work_date': '2024-01-15',
            'created_at': '2024-01-15 09:00:00'
        }
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        self.assertIn('Check-in successful', response_data['message'])
        self.assertEqual(response_data['attendance_id'], 1)
        
        # Verify repository methods were called correctly
        mock_attendance_repo.get_today_attendance.assert_called_with(1)
        mock_attendance_repo.create_checkin.assert_called_once_with(1)
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_prevent_duplicate_checkin_workflow(self, mock_get_user, mock_attendance_repo):
        """Test that duplicate check-in is prevented in complete workflow"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        
        # Mock that employee is already checked in
        mock_attendance_repo.get_today_attendance.return_value = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': '2024-01-15 08:00:00',
            'check_out_time': None,
            'work_date': '2024-01-15',
            'created_at': '2024-01-15 08:00:00'
        }
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('already checked in today', response_data['error'])
        
        # Verify create_checkin was NOT called
        mock_attendance_repo.create_checkin.assert_not_called()
    
    @patch('app.attendance_repo')
    @patch('flask_login.utils._get_user')
    def test_prevent_checkin_after_completion_workflow(self, mock_get_user, mock_attendance_repo):
        """Test that check-in is prevented after completion in complete workflow"""
        # Arrange
        mock_get_user.return_value = self.test_employee
        
        # Mock that employee has completed attendance
        mock_attendance_repo.get_today_attendance.return_value = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': '2024-01-15 08:00:00',
            'check_out_time': '2024-01-15 17:00:00',
            'work_date': '2024-01-15',
            'created_at': '2024-01-15 08:00:00'
        }
        
        # Act
        with self.app.test_request_context():
            response = self.client.post('/check-in')
        
        # Assert
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('already completed attendance', response_data['error'])
        
        # Verify create_checkin was NOT called
        mock_attendance_repo.create_checkin.assert_not_called()


if __name__ == '__main__':
    unittest.main()