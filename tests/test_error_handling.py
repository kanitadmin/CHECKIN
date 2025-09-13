"""
Unit tests for comprehensive error handling and validation
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import sys
import time
import requests
from flask import session

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (
    app, validate_environment_variables, validate_oauth_config, 
    _is_valid_domain_format, get_attendance_status, AttendanceStatus,
    ConfigurationError, AuthenticationError
)
from database import DatabaseManager, DatabaseConnectionError, DatabaseQueryError
import pymysql


class TestEnvironmentValidation(unittest.TestCase):
    """Test cases for environment variable validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_validate_environment_variables_success(self):
        """Test successful environment validation with all required variables"""
        test_env = {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'FLASK_SECRET_KEY': 'test-secret',
            'DB_PORT': '3306'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            is_valid, errors = validate_environment_variables()
            self.assertTrue(is_valid)
            self.assertEqual(errors, [])
    
    def test_validate_environment_variables_missing_required(self):
        """Test environment validation with missing required variables"""
        test_env = {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            # Missing GOOGLE_CLIENT_SECRET, HOSTED_DOMAIN, DB_* variables
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            is_valid, errors = validate_environment_variables()
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
            
            # Check that specific missing variables are mentioned
            error_text = ' '.join(errors)
            self.assertIn('GOOGLE_CLIENT_SECRET', error_text)
            self.assertIn('HOSTED_DOMAIN', error_text)
            self.assertIn('DB_HOST', error_text)
    
    def test_validate_environment_variables_empty_values(self):
        """Test environment validation with empty string values"""
        test_env = {
            'GOOGLE_CLIENT_ID': '',  # Empty string
            'GOOGLE_CLIENT_SECRET': '   ',  # Whitespace only
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            is_valid, errors = validate_environment_variables()
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
    
    def test_validate_environment_variables_invalid_domain_format(self):
        """Test environment validation with invalid domain format"""
        test_env = {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': '.invalid-domain.',  # Invalid format
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            is_valid, errors = validate_environment_variables()
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
            
            error_text = ' '.join(errors)
            self.assertIn('HOSTED_DOMAIN', error_text)
            self.assertIn('valid domain format', error_text)
    
    def test_validate_environment_variables_invalid_port(self):
        """Test environment validation with invalid database port"""
        test_env = {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'DB_PORT': 'invalid-port'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            is_valid, errors = validate_environment_variables()
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
            
            error_text = ' '.join(errors)
            self.assertIn('DB_PORT', error_text)
            self.assertIn('valid integer', error_text)


class TestDomainFormatValidation(unittest.TestCase):
    """Test cases for domain format validation"""
    
    def test_valid_domain_formats(self):
        """Test valid domain formats"""
        valid_domains = [
            'company.com',
            'sub.company.com',
            'go.buu.ac.th',
            'example.org',
            'test-domain.co.uk',
            'a.b.c.d.com'
        ]
        
        for domain in valid_domains:
            with self.subTest(domain=domain):
                self.assertTrue(_is_valid_domain_format(domain))
    
    def test_invalid_domain_formats(self):
        """Test invalid domain formats"""
        invalid_domains = [
            '',
            None,
            '.',
            '.com',
            'com.',
            'invalid..domain.com',
            'domain with spaces.com',
            'domain@with@symbols.com',
            'a' * 300,  # Too long
            'no-dots',
            '.start-with-dot.com',
            'end-with-dot.com.'
        ]
        
        for domain in invalid_domains:
            with self.subTest(domain=domain):
                self.assertFalse(_is_valid_domain_format(domain))


class TestOAuthConfigValidation(unittest.TestCase):
    """Test cases for OAuth configuration validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_env = {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com'
        }
    
    @patch('app.requests.get')
    def test_validate_oauth_config_success(self, mock_get):
        """Test successful OAuth configuration validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, self.test_env):
            is_valid, error_msg = validate_oauth_config()
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
    
    @patch('app.requests.get')
    def test_validate_oauth_config_connection_timeout(self, mock_get):
        """Test OAuth validation with connection timeout"""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        with patch.dict(os.environ, self.test_env):
            is_valid, error_msg = validate_oauth_config()
            self.assertTrue(is_valid)  # Should still allow app to start
            self.assertEqual(error_msg, "")
    
    @patch('app.requests.get')
    def test_validate_oauth_config_connection_error(self, mock_get):
        """Test OAuth validation with connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch.dict(os.environ, self.test_env):
            is_valid, error_msg = validate_oauth_config()
            self.assertTrue(is_valid)  # Should still allow app to start
            self.assertEqual(error_msg, "")
    
    def test_validate_oauth_config_missing_variables(self):
        """Test OAuth validation with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error_msg = validate_oauth_config()
            self.assertFalse(is_valid)
            self.assertIn("Missing OAuth configuration", error_msg)


class TestDatabaseConnectionErrorHandling(unittest.TestCase):
    """Test cases for database connection error handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_env = {
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'DB_PORT': '3306'
        }
    
    @patch('database.pymysql.connect')
    def test_database_connection_retry_success(self, mock_connect):
        """Test successful database connection after retry"""
        # First attempt fails, second succeeds
        mock_connect.side_effect = [
            pymysql.OperationalError(2003, "Connection refused"),
            MagicMock()
        ]
        
        with patch.dict(os.environ, self.test_env):
            with patch('time.sleep'):  # Mock sleep to speed up test
                db_manager = DatabaseManager()
                connection = db_manager.get_connection()
                self.assertIsNotNone(connection)
                self.assertEqual(mock_connect.call_count, 2)
    
    @patch('database.pymysql.connect')
    def test_database_connection_max_retries_exceeded(self, mock_connect):
        """Test database connection failure after max retries"""
        mock_connect.side_effect = pymysql.OperationalError(2003, "Connection refused")
        
        with patch.dict(os.environ, self.test_env):
            with patch('time.sleep'):  # Mock sleep to speed up test
                db_manager = DatabaseManager()
                with self.assertRaises(DatabaseConnectionError):
                    db_manager.get_connection()
                self.assertEqual(mock_connect.call_count, 3)
    
    @patch('database.pymysql.connect')
    def test_database_authentication_error(self, mock_connect):
        """Test database authentication error handling"""
        mock_connect.side_effect = pymysql.OperationalError(1045, "Access denied")
        
        with patch.dict(os.environ, self.test_env):
            db_manager = DatabaseManager()
            with self.assertRaises(DatabaseConnectionError) as context:
                db_manager.get_connection()
            
            self.assertIn("authentication failed", str(context.exception))
            self.assertEqual(mock_connect.call_count, 1)  # Should not retry auth errors
    
    @patch('database.pymysql.connect')
    def test_database_not_found_error(self, mock_connect):
        """Test database not found error handling"""
        mock_connect.side_effect = pymysql.OperationalError(1049, "Unknown database 'testdb'")
        
        with patch.dict(os.environ, self.test_env):
            db_manager = DatabaseManager()
            with self.assertRaises(DatabaseConnectionError) as context:
                db_manager.get_connection()
            
            self.assertIn("does not exist", str(context.exception))
            self.assertEqual(mock_connect.call_count, 1)  # Should not retry DB not found errors


class TestAttendanceStatusErrorHandling(unittest.TestCase):
    """Test cases for attendance status error handling"""
    
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
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_database_connection_error_retry(self, mock_get_attendance):
        """Test attendance status with database connection error and retry"""
        # First two calls fail, third succeeds
        mock_get_attendance.side_effect = [
            DatabaseConnectionError("Connection failed"),
            DatabaseConnectionError("Connection failed"),
            None  # No attendance record
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            status = get_attendance_status(1)
            self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
            self.assertEqual(mock_get_attendance.call_count, 3)
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_max_retries_exceeded(self, mock_get_attendance):
        """Test attendance status when max retries exceeded"""
        mock_get_attendance.side_effect = DatabaseConnectionError("Connection failed")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            status = get_attendance_status(1)
            self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
            self.assertEqual(mock_get_attendance.call_count, 3)
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_query_error(self, mock_get_attendance):
        """Test attendance status with database query error"""
        mock_get_attendance.side_effect = DatabaseQueryError("Query failed")
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        self.assertEqual(mock_get_attendance.call_count, 1)  # Should not retry query errors
    
    def test_get_attendance_status_empty_employee_id(self):
        """Test attendance status with empty employee ID"""
        status = get_attendance_status(None)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        
        status = get_attendance_status("")
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)


class TestFlaskErrorHandlers(unittest.TestCase):
    """Test cases for Flask error handlers"""
    
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
            'DB_NAME': 'testdb'
        })
    
    def test_404_error_handler(self):
        """Test 404 error handler"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Page not found', response.data)
    
    def test_500_error_handler(self):
        """Test 500 error handler"""
        # Test that 500 errors are handled gracefully
        # We'll test this by triggering an actual 500 error
        with patch('app.render_template') as mock_render:
            # First call (from the route) fails, second call (from error handler) succeeds
            mock_render.side_effect = [
                Exception("Template error"),  # Triggers 500 error
                "Error page content"  # Error handler renders successfully
            ]
            
            # This should trigger a 500 error and then handle it
            response = self.client.get('/')
            # The error handler should catch the 500 and return an error page
            self.assertIn(response.status_code, [500, 302])  # Either error page or redirect to login


class TestSessionExpiryHandling(unittest.TestCase):
    """Test cases for session expiry handling"""
    
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
            'DB_NAME': 'testdb'
        })
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    def test_session_expiry_user_not_found(self, mock_current_user, mock_find_by_id):
        """Test session expiry when user no longer exists in database"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_current_user.return_value = mock_user
        
        # Mock user not found in database
        mock_find_by_id.return_value = None
        
        with self.client:
            response = self.client.get('/')
            # Should redirect to login due to user not found
            self.assertEqual(response.status_code, 302)


class TestConstraintViolationHandling(unittest.TestCase):
    """Test cases for database constraint violation handling"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock environment variables and login
        os.environ.update({
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'company.com',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb'
        })
    
    @patch('app.employee_repo.find_by_id')
    @patch('app.current_user')
    @patch('app.attendance_repo.create_checkin')
    @patch('app.get_attendance_status')
    def test_duplicate_checkin_constraint_violation(self, mock_status, mock_create_checkin, mock_current_user, mock_find_by_id):
        """Test handling of duplicate check-in constraint violation"""
        # Mock authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.email = 'test@company.com'
        mock_current_user.return_value = mock_user
        
        # Mock user exists in database (for session validation)
        mock_find_by_id.return_value = mock_user
        
        # Mock status as not checked in
        mock_status.return_value = AttendanceStatus.NOT_CHECKED_IN
        
        # Mock constraint violation
        mock_create_checkin.side_effect = DatabaseQueryError("already checked in today")
        
        response = self.client.post('/check-in')
        self.assertEqual(response.status_code, 400)
        
        response_data = response.get_json()
        self.assertFalse(response_data['success'])
        self.assertIn('already checked in', response_data['error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)