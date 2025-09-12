"""
Unit tests for error handling functions (without Flask context)
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import sys
import time
import requests
import pymysql

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (
    validate_environment_variables, validate_oauth_config, 
    _is_valid_domain_format, get_attendance_status, AttendanceStatus,
    validate_company_domain
)
from database import DatabaseManager, DatabaseConnectionError, DatabaseQueryError


class TestEnvironmentValidationUnit(unittest.TestCase):
    """Unit tests for environment variable validation"""
    
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
            # Missing other required variables
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


class TestDomainValidationUnit(unittest.TestCase):
    """Unit tests for domain validation"""
    
    def test_valid_domain_formats(self):
        """Test valid domain formats"""
        valid_domains = [
            'company.com',
            'sub.company.com',
            'go.buu.ac.th',
            'example.org',
            'test-domain.co.uk'
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
            'no-dots'
        ]
        
        for domain in invalid_domains:
            with self.subTest(domain=domain):
                self.assertFalse(_is_valid_domain_format(domain))
    
    def test_company_domain_validation_success(self):
        """Test successful company domain validation"""
        with patch.dict(os.environ, {'HOSTED_DOMAIN': 'company.com'}):
            is_valid, error = validate_company_domain('user@company.com')
            self.assertTrue(is_valid)
            self.assertEqual(error, '')
    
    def test_company_domain_validation_failure(self):
        """Test company domain validation failure"""
        with patch.dict(os.environ, {'HOSTED_DOMAIN': 'company.com'}):
            is_valid, error = validate_company_domain('user@other.com')
            self.assertFalse(is_valid)
            self.assertIn('company.com', error)
    
    def test_company_domain_validation_invalid_email(self):
        """Test company domain validation with invalid email"""
        with patch.dict(os.environ, {'HOSTED_DOMAIN': 'company.com'}):
            is_valid, error = validate_company_domain('invalid-email')
            self.assertFalse(is_valid)
            self.assertIn('format', error.lower())


class TestAttendanceStatusUnit(unittest.TestCase):
    """Unit tests for attendance status handling"""
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_not_checked_in(self, mock_get_attendance):
        """Test attendance status when not checked in"""
        mock_get_attendance.return_value = None
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_checked_in(self, mock_get_attendance):
        """Test attendance status when checked in but not out"""
        mock_get_attendance.return_value = {
            'check_in_time': '09:00:00',
            'check_out_time': None
        }
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.CHECKED_IN)
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_completed(self, mock_get_attendance):
        """Test attendance status when completed"""
        mock_get_attendance.return_value = {
            'check_in_time': '09:00:00',
            'check_out_time': '17:00:00'
        }
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.COMPLETED)
    
    @patch('time.sleep')
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_retry_on_connection_error(self, mock_get_attendance, mock_sleep):
        """Test attendance status retry on connection error"""
        # First two calls fail, third succeeds
        mock_get_attendance.side_effect = [
            DatabaseConnectionError("Connection failed"),
            DatabaseConnectionError("Connection failed"),
            None
        ]
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        self.assertEqual(mock_get_attendance.call_count, 3)
    
    @patch('time.sleep')
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_max_retries_exceeded(self, mock_get_attendance, mock_sleep):
        """Test attendance status when max retries exceeded"""
        mock_get_attendance.side_effect = DatabaseConnectionError("Connection failed")
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        self.assertEqual(mock_get_attendance.call_count, 3)
    
    @patch('app.attendance_repo.get_today_attendance')
    def test_get_attendance_status_query_error_no_retry(self, mock_get_attendance):
        """Test attendance status with query error (no retry)"""
        mock_get_attendance.side_effect = DatabaseQueryError("Query failed")
        
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        self.assertEqual(mock_get_attendance.call_count, 1)  # Should not retry
    
    def test_get_attendance_status_empty_employee_id(self):
        """Test attendance status with empty employee ID"""
        status = get_attendance_status(None)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        
        status = get_attendance_status("")
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)


class TestDatabaseConnectionRetryUnit(unittest.TestCase):
    """Unit tests for database connection retry logic"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_env = {
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'DB_PORT': '3306'
        }
    
    @patch('time.sleep')
    @patch('database.pymysql.connect')
    def test_database_connection_retry_success(self, mock_connect, mock_sleep):
        """Test successful database connection after retry"""
        # First attempt fails, second succeeds
        mock_connect.side_effect = [
            pymysql.OperationalError(2003, "Connection refused"),
            MagicMock()
        ]
        
        with patch.dict(os.environ, self.test_env):
            db_manager = DatabaseManager()
            connection = db_manager.get_connection()
            self.assertIsNotNone(connection)
            self.assertEqual(mock_connect.call_count, 2)
    
    @patch('time.sleep')
    @patch('database.pymysql.connect')
    def test_database_connection_max_retries_exceeded(self, mock_connect, mock_sleep):
        """Test database connection failure after max retries"""
        mock_connect.side_effect = pymysql.OperationalError(2003, "Connection refused")
        
        with patch.dict(os.environ, self.test_env):
            db_manager = DatabaseManager()
            with self.assertRaises(DatabaseConnectionError):
                db_manager.get_connection()
            self.assertEqual(mock_connect.call_count, 3)
    
    @patch('database.pymysql.connect')
    def test_database_authentication_error_no_retry(self, mock_connect):
        """Test database authentication error (no retry)"""
        mock_connect.side_effect = pymysql.OperationalError(1045, "Access denied")
        
        with patch.dict(os.environ, self.test_env):
            db_manager = DatabaseManager()
            with self.assertRaises(DatabaseConnectionError) as context:
                db_manager.get_connection()
            
            self.assertIn("authentication failed", str(context.exception))
            self.assertEqual(mock_connect.call_count, 1)  # Should not retry
    
    @patch('database.pymysql.connect')
    def test_database_not_found_error_no_retry(self, mock_connect):
        """Test database not found error (no retry)"""
        mock_connect.side_effect = pymysql.OperationalError(1049, "Unknown database 'testdb'")
        
        with patch.dict(os.environ, self.test_env):
            db_manager = DatabaseManager()
            with self.assertRaises(DatabaseConnectionError) as context:
                db_manager.get_connection()
            
            self.assertIn("does not exist", str(context.exception))
            self.assertEqual(mock_connect.call_count, 1)  # Should not retry


class TestOAuthConfigValidationUnit(unittest.TestCase):
    """Unit tests for OAuth configuration validation"""
    
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
    def test_validate_oauth_config_timeout(self, mock_get):
        """Test OAuth validation with timeout"""
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


if __name__ == '__main__':
    unittest.main(verbosity=2)