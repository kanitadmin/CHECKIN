"""
Integration tests for main dashboard functionality
Tests dashboard logic with different attendance states and user interactions
"""
import pytest
import os
import sys
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from flask import session

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, AttendanceStatus
from models import Employee, EmployeeRepository, AttendanceRepository
from database import DatabaseManager


class TestDashboardIntegration:
    """Integration tests for dashboard functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = True  # Disable login requirement for testing
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture
    def mock_employee(self):
        """Create mock employee for testing"""
        return Employee(
            id=1,
            google_id='test_google_id',
            email='test@company.com',
            name='Test User',
            picture_url='https://example.com/avatar.jpg'
        )
    
    @pytest.fixture
    def mock_attendance_repo(self):
        """Create mock attendance repository"""
        return MagicMock(spec=AttendanceRepository)
    
    @pytest.fixture
    def mock_employee_repo(self):
        """Create mock employee repository"""
        return MagicMock(spec=EmployeeRepository)
    
    def test_dashboard_not_checked_in_state(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard displays correctly when user hasn't checked in"""
        # Mock the current user and attendance status
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            # Mock no attendance record for today
            mock_attendance_repo.get_today_attendance.return_value = None
            mock_attendance_repo.get_recent_history.return_value = []
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify response
            assert response.status_code == 200
            assert b'Ready to Start Your Day' in response.data
            assert b'Check In' in response.data
            assert b'status-not-checked-in' in response.data
            assert b'Check Out' not in response.data
            
            # Verify repository calls (called twice: once in get_attendance_status, once in index route)
            assert mock_attendance_repo.get_today_attendance.call_count == 2
            mock_attendance_repo.get_recent_history.assert_called_once_with(1, days=14)
    
    def test_dashboard_checked_in_state(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard displays correctly when user is checked in but not out"""
        check_in_time = datetime(2023, 12, 15, 9, 0, 0)
        
        # Mock attendance record with check-in but no check-out
        today_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': check_in_time,
            'check_out_time': None,
            'work_date': date(2023, 12, 15)
        }
        
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            mock_attendance_repo.get_today_attendance.return_value = today_attendance
            mock_attendance_repo.get_recent_history.return_value = [today_attendance]
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify response
            assert response.status_code == 200
            assert b'You\'re Checked In' in response.data
            assert b'Check Out' in response.data
            assert b'09:00 AM' in response.data  # Check formatted time
            assert b'status-checked-in' in response.data
            # Check that the Check In button is not displayed (but ignore JavaScript function names)
            assert b'<button id="check-in-btn"' not in response.data
            
            # Verify repository calls (called twice: once in get_attendance_status, once in index route)
            assert mock_attendance_repo.get_today_attendance.call_count == 2
            mock_attendance_repo.get_recent_history.assert_called_once_with(1, days=14)
    
    def test_dashboard_completed_state(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard displays correctly when user has completed attendance"""
        check_in_time = datetime(2023, 12, 15, 9, 0, 0)
        check_out_time = datetime(2023, 12, 15, 17, 30, 0)
        
        # Mock attendance record with both check-in and check-out
        today_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': check_in_time,
            'check_out_time': check_out_time,
            'work_date': date(2023, 12, 15)
        }
        
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            mock_attendance_repo.get_today_attendance.return_value = today_attendance
            mock_attendance_repo.get_recent_history.return_value = [today_attendance]
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify response
            assert response.status_code == 200
            assert b'Attendance Complete' in response.data
            assert b'Attendance completed for today' in response.data
            assert b'status-completed' in response.data
            # Check that neither button is displayed (but ignore JavaScript function names)
            assert b'<button id="check-in-btn"' not in response.data
            assert b'<button id="check-out-btn"' not in response.data
            
            # Verify repository calls (called twice: once in get_attendance_status, once in index route)
            assert mock_attendance_repo.get_today_attendance.call_count == 2
            mock_attendance_repo.get_recent_history.assert_called_once_with(1, days=14)
    
    def test_dashboard_attendance_history_display(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard displays attendance history correctly"""
        # Create mock attendance history
        history = [
            {
                'id': 3,
                'employee_id': 1,
                'check_in_time': datetime(2023, 12, 15, 9, 0, 0),
                'check_out_time': datetime(2023, 12, 15, 17, 30, 0),
                'work_date': date(2023, 12, 15)
            },
            {
                'id': 2,
                'employee_id': 1,
                'check_in_time': datetime(2023, 12, 14, 8, 45, 0),
                'check_out_time': datetime(2023, 12, 14, 17, 15, 0),
                'work_date': date(2023, 12, 14)
            },
            {
                'id': 1,
                'employee_id': 1,
                'check_in_time': datetime(2023, 12, 13, 9, 15, 0),
                'check_out_time': None,  # Not checked out
                'work_date': date(2023, 12, 13)
            }
        ]
        
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            mock_attendance_repo.get_today_attendance.return_value = None
            mock_attendance_repo.get_recent_history.return_value = history
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify response contains history data
            assert response.status_code == 200
            assert b'Recent Attendance History' in response.data
            assert b'Friday, December 15, 2023' in response.data
            assert b'09:00 AM' in response.data
            assert b'05:30 PM' in response.data
            assert b'Not checked out' in response.data
            assert b'Complete' in response.data
            assert b'In Progress' in response.data
    
    def test_dashboard_no_attendance_history(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard displays message when no attendance history exists"""
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            mock_attendance_repo.get_today_attendance.return_value = None
            mock_attendance_repo.get_recent_history.return_value = []
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify response shows no history message
            assert response.status_code == 200
            assert b'No attendance history found' in response.data
            assert b'Your check-ins will appear here' in response.data
    
    def test_dashboard_error_handling(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard handles errors gracefully"""
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            # Mock repository to raise exception
            mock_attendance_repo.get_today_attendance.side_effect = Exception("Database error")
            mock_attendance_repo.get_recent_history.return_value = []
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify response still works with error handling
            assert response.status_code == 200
            assert b'Ready to Start Your Day' in response.data  # Default to not checked in
    
    def test_dashboard_user_info_display(self, client, mock_employee, mock_attendance_repo):
        """Test dashboard displays user information correctly"""
        with patch('app.current_user', mock_employee), \
             patch('app.attendance_repo', mock_attendance_repo):
            
            mock_attendance_repo.get_today_attendance.return_value = None
            mock_attendance_repo.get_recent_history.return_value = []
            
            # Make request to dashboard
            response = client.get('/')
            
            # Verify dashboard loads correctly (user info display is tested in browser tests)
            assert response.status_code == 200
            assert b'Employee Check-in System' in response.data
            assert b'Ready to Start Your Day' in response.data
    
    def test_dashboard_requires_authentication(self, client):
        """Test dashboard redirects unauthenticated users to login"""
        # Temporarily enable login requirement
        with patch.object(app.config, 'get', side_effect=lambda key, default=None: False if key == 'LOGIN_DISABLED' else default):
            # Make request without authentication
            response = client.get('/')
            
            # Verify redirect to login
            assert response.status_code == 302
            assert '/login' in response.location
    
    def test_get_attendance_status_function(self):
        """Test the get_attendance_status helper function"""
        from app import get_attendance_status
        
        mock_repo = MagicMock()
        
        with patch('app.attendance_repo', mock_repo):
            # Test not checked in
            mock_repo.get_today_attendance.return_value = None
            status = get_attendance_status(1)
            assert status == AttendanceStatus.NOT_CHECKED_IN
            
            # Test checked in but not out
            mock_repo.get_today_attendance.return_value = {
                'check_in_time': datetime.now(),
                'check_out_time': None
            }
            status = get_attendance_status(1)
            assert status == AttendanceStatus.CHECKED_IN
            
            # Test completed
            mock_repo.get_today_attendance.return_value = {
                'check_in_time': datetime.now(),
                'check_out_time': datetime.now()
            }
            status = get_attendance_status(1)
            assert status == AttendanceStatus.COMPLETED
            
            # Test error handling
            mock_repo.get_today_attendance.side_effect = Exception("Database error")
            status = get_attendance_status(1)
            assert status == AttendanceStatus.NOT_CHECKED_IN  # Default on error
    
    def test_dashboard_time_formatting(self, client, mock_employee, mock_attendance_repo):
        """Test that times are formatted correctly in the dashboard"""
        # Test various time formats
        test_times = [
            (datetime(2023, 12, 15, 9, 0, 0), b'09:00 AM'),
            (datetime(2023, 12, 15, 13, 30, 0), b'01:30 PM'),
            (datetime(2023, 12, 15, 0, 15, 0), b'12:15 AM'),
            (datetime(2023, 12, 15, 23, 45, 0), b'11:45 PM')
        ]
        
        for check_in_time, expected_format in test_times:
            today_attendance = {
                'id': 1,
                'employee_id': 1,
                'check_in_time': check_in_time,
                'check_out_time': None,
                'work_date': date(2023, 12, 15)
            }
            
            with patch('app.current_user', mock_employee), \
                 patch('app.attendance_repo', mock_attendance_repo):
                
                mock_attendance_repo.get_today_attendance.return_value = today_attendance
                mock_attendance_repo.get_recent_history.return_value = []
                
                # Make request to dashboard
                response = client.get('/')
                
                # Verify time formatting
                assert response.status_code == 200
                assert expected_format in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])