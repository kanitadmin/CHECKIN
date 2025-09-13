"""
Unit tests for session expiry and authentication edge cases
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import sys
from flask import session

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import DatabaseConnectionError, DatabaseQueryError


class TestSessionExpiryScenarios(unittest.TestCase):
    """Test cases for various session expiry scenarios"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock environment variables
        os.environ.update({
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'FLASK_SECRET_KEY': 'test-secret'
        })
    
    def test_unauthenticated_user_redirect(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    def test_check_in_with_invalid_session(self):
        """Test check-in with invalid session"""
        response = self.client.post('/check-in')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_check_out_with_invalid_session(self):
        """Test check-out with invalid session"""
        response = self.client.post('/check-out')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    def test_check_in_with_none_user_id(self, mock_current_user, mock_find_by_id):
        """Test check-in when current_user.id is None"""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = None  # Invalid user ID
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        response = self.client.post('/check-in')
        self.assertEqual(response.status_code, 401)
        
        response_data = response.get_json()
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid session', response_data['error'])
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    def test_check_out_with_none_user_id(self, mock_current_user, mock_find_by_id):
        """Test check-out when current_user.id is None"""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = None  # Invalid user ID
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        response = self.client.post('/check-out')
        self.assertEqual(response.status_code, 401)
        
        response_data = response.get_json()
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid session', response_data['error'])


class TestDatabaseConnectionRetryScenarios(unittest.TestCase):
    """Test cases for database connection retry scenarios"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock environment variables
        os.environ.update({
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'FLASK_SECRET_KEY': 'test-secret'
        })
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    @patch('app.attendance_repo.create_checkin')
    @patch('app.get_attendance_status')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_check_in_database_connection_retry_success(self, mock_sleep, mock_status, mock_create_checkin, mock_current_user, mock_find_by_id):
        """Test check-in with database connection retry that eventually succeeds"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.email = 'test@company.com'
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        # Mock status as not checked in
        mock_status.return_value = 'not_checked_in'
        
        # Mock connection failure then success
        mock_create_checkin.side_effect = [
            DatabaseConnectionError("Connection failed"),
            DatabaseConnectionError("Connection failed"),
            {
                'id': 1,
                'check_in_time': Mock(strftime=Mock(return_value='09:00 AM'))
            }
        ]
        
        response = self.client.post('/check-in')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.get_json()
        self.assertTrue(response_data['success'])
        self.assertEqual(mock_create_checkin.call_count, 3)
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    @patch('app.attendance_repo.create_checkin')
    @patch('app.get_attendance_status')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_check_in_database_connection_retry_failure(self, mock_sleep, mock_status, mock_create_checkin, mock_current_user, mock_find_by_id):
        """Test check-in with database connection retry that fails all attempts"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.email = 'test@company.com'
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        # Mock status as not checked in
        mock_status.return_value = 'not_checked_in'
        
        # Mock connection failure for all attempts
        mock_create_checkin.side_effect = DatabaseConnectionError("Connection failed")
        
        response = self.client.post('/check-in')
        self.assertEqual(response.status_code, 503)
        
        response_data = response.get_json()
        self.assertFalse(response_data['success'])
        self.assertIn('Database connection issue', response_data['error'])
        self.assertEqual(mock_create_checkin.call_count, 3)
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    @patch('app.attendance_repo.update_checkout')
    @patch('app.get_attendance_status')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_check_out_database_connection_retry_success(self, mock_sleep, mock_status, mock_update_checkout, mock_current_user, mock_find_by_id):
        """Test check-out with database connection retry that eventually succeeds"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.email = 'test@company.com'
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        # Mock status as checked in
        mock_status.return_value = 'checked_in'
        
        # Mock connection failure then success
        mock_update_checkout.side_effect = [
            DatabaseConnectionError("Connection failed"),
            {
                'id': 1,
                'check_in_time': Mock(strftime=Mock(return_value='09:00 AM')),
                'check_out_time': Mock(strftime=Mock(return_value='05:00 PM'))
            }
        ]
        
        response = self.client.post('/check-out')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.get_json()
        self.assertTrue(response_data['success'])
        self.assertEqual(mock_update_checkout.call_count, 2)


class TestUserLoadErrorHandling(unittest.TestCase):
    """Test cases for user loader error handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        
        # Mock environment variables
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb'
        })
    
    @patch('app.employee_repo.find_by_id')
    def test_load_user_with_invalid_user_id_format(self, mock_find_by_id):
        """Test user loader with invalid user ID format"""
        from app import load_user
        
        # Test with non-numeric string
        result = load_user('invalid-id')
        self.assertIsNone(result)
        mock_find_by_id.assert_not_called()
        
        # Test with None
        result = load_user(None)
        self.assertIsNone(result)
        mock_find_by_id.assert_not_called()
        
        # Test with empty string
        result = load_user('')
        self.assertIsNone(result)
        mock_find_by_id.assert_not_called()
    
    @patch('app.employee_repo.find_by_id')
    def test_load_user_with_database_connection_error(self, mock_find_by_id):
        """Test user loader with database connection error"""
        from app import load_user
        
        mock_find_by_id.side_effect = DatabaseConnectionError("Connection failed")
        
        result = load_user('1')
        self.assertIsNone(result)
        mock_find_by_id.assert_called_once_with(1)
    
    @patch('app.employee_repo.find_by_id')
    def test_load_user_with_database_query_error(self, mock_find_by_id):
        """Test user loader with database query error"""
        from app import load_user
        
        mock_find_by_id.side_effect = DatabaseQueryError("Query failed")
        
        result = load_user('1')
        self.assertIsNone(result)
        mock_find_by_id.assert_called_once_with(1)
    
    @patch('app.employee_repo.find_by_id')
    def test_load_user_with_unexpected_error(self, mock_find_by_id):
        """Test user loader with unexpected error"""
        from app import load_user
        
        mock_find_by_id.side_effect = Exception("Unexpected error")
        
        result = load_user('1')
        self.assertIsNone(result)
        mock_find_by_id.assert_called_once_with(1)


class TestDashboardErrorHandling(unittest.TestCase):
    """Test cases for dashboard error handling"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock environment variables
        os.environ.update({
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'FLASK_SECRET_KEY': 'test-secret'
        })
    
    @patch('app.current_user')
    def test_dashboard_with_invalid_user_session(self, mock_current_user):
        """Test dashboard access with invalid user session"""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = None  # Invalid user ID
        mock_current_user.return_value = mock_user
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.attendance_repo.get_recent_history')
    @patch('app.current_user')
    @patch('app.attendance_repo.get_today_attendance')
    @patch('app.get_attendance_status')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_dashboard_with_database_connection_retry(self, mock_sleep, mock_status, mock_get_today, mock_current_user, mock_get_history, mock_find_by_id):
        """Test dashboard with database connection retry"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.email = 'test@company.com'
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        # Mock status
        mock_status.return_value = 'not_checked_in'
        
        # Mock history
        mock_get_history.return_value = []
        
        # Mock connection failure then success
        mock_get_today.side_effect = [
            DatabaseConnectionError("Connection failed"),
            None  # No attendance record
        ]
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_get_today.call_count, 2)
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    @patch('app.attendance_repo.get_recent_history')
    @patch('app.attendance_repo.get_today_attendance')
    @patch('app.get_attendance_status')
    def test_dashboard_with_history_error(self, mock_status, mock_get_today, mock_get_history, mock_current_user, mock_find_by_id):
        """Test dashboard when attendance history fails to load"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.email = 'test@company.com'
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        # Mock status and today's attendance
        mock_status.return_value = 'not_checked_in'
        mock_get_today.return_value = None
        
        # Mock history error
        mock_get_history.side_effect = DatabaseConnectionError("Connection failed")
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Should still render page even if history fails


if __name__ == '__main__':
    unittest.main(verbosity=2)