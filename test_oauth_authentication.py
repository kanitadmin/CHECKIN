"""
Unit tests for OAuth authentication functionality
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import validate_company_domain, app


class TestDomainValidation(unittest.TestCase):
    """Test cases for domain validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variable for testing
        self.original_hosted_domain = os.getenv('HOSTED_DOMAIN')
        os.environ['HOSTED_DOMAIN'] = 'go.buu.ac.th'
    
    def tearDown(self):
        """Clean up test environment"""
        if self.original_hosted_domain:
            os.environ['HOSTED_DOMAIN'] = self.original_hosted_domain
        elif 'HOSTED_DOMAIN' in os.environ:
            del os.environ['HOSTED_DOMAIN']
    
    def test_valid_company_domain_acceptance(self):
        """Test that valid company domain emails are accepted"""
        valid_emails = [
            'john.doe@go.buu.ac.th',
            'jane.smith@go.buu.ac.th',
            'admin@go.buu.ac.th'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                is_valid, error_message = validate_company_domain(email)
                self.assertTrue(is_valid, f"Email {email} should be valid")
                self.assertEqual(error_message, "", f"No error message expected for {email}")
    
    def test_invalid_domain_rejection(self):
        """Test that invalid domain emails are rejected"""
        invalid_emails = [
            'john.doe@gmail.com',
            'jane.smith@yahoo.com',
            'admin@other-company.com',
            'user@buu.ac.th'  # Missing 'go.' subdomain
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                is_valid, error_message = validate_company_domain(email)
                self.assertFalse(is_valid, f"Email {email} should be invalid")
                self.assertIn("go.buu.ac.th", error_message, f"Error message should mention company domain for {email}")
    
    def test_case_insensitive_domain_validation(self):
        """Test that domain validation is case insensitive"""
        test_cases = [
            'user@GO.BUU.AC.TH',
            'user@Go.Buu.Ac.Th',
            'user@go.BUU.ac.th'
        ]
        
        for email in test_cases:
            with self.subTest(email=email):
                is_valid, error_message = validate_company_domain(email)
                self.assertTrue(is_valid, f"Email {email} should be valid (case insensitive)")
                self.assertEqual(error_message, "")
    
    def test_empty_email_handling(self):
        """Test handling of empty or None email"""
        test_cases = [None, '', '   ']
        
        for email in test_cases:
            with self.subTest(email=email):
                is_valid, error_message = validate_company_domain(email)
                self.assertFalse(is_valid, f"Email '{email}' should be invalid")
                self.assertIn("required", error_message.lower())
    
    def test_invalid_email_format(self):
        """Test handling of malformed email addresses"""
        invalid_formats = [
            'not-an-email',
            '@go.buu.ac.th',
            'user@',
            'user@@go.buu.ac.th',
            'user.go.buu.ac.th'  # Missing @
        ]
        
        for email in invalid_formats:
            with self.subTest(email=email):
                is_valid, error_message = validate_company_domain(email)
                self.assertFalse(is_valid, f"Email '{email}' should be invalid")
                self.assertIn("format", error_message.lower())
    
    def test_missing_hosted_domain_config(self):
        """Test behavior when HOSTED_DOMAIN environment variable is not set"""
        # Remove the environment variable
        if 'HOSTED_DOMAIN' in os.environ:
            del os.environ['HOSTED_DOMAIN']
        
        is_valid, error_message = validate_company_domain('user@go.buu.ac.th')
        self.assertFalse(is_valid)
        self.assertIn("not configured", error_message.lower())


class TestOAuthConfiguration(unittest.TestCase):
    """Test cases for OAuth configuration"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Set up required environment variables for testing
        os.environ.update({
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'go.buu.ac.th',
            'FLASK_SECRET_KEY': 'test-secret-key'
        })
    
    def test_login_route_displays_login_page(self):
        """Test that /login route displays the login page"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login with Google', response.data)
        self.assertIn(b'Employee Check-in System', response.data)
    
    @patch('app.google.authorize_redirect')
    def test_auth_google_route_redirects_to_oauth(self, mock_authorize):
        """Test that /auth/google route initiates OAuth flow"""
        mock_authorize.return_value = 'mocked_redirect'
        
        response = self.client.get('/auth/google')
        
        # Check that authorize_redirect was called
        mock_authorize.assert_called_once()
        
        # Check that state parameter is set in session
        with self.client.session_transaction() as sess:
            self.assertIn('oauth_state', sess)
            self.assertIsNotNone(sess['oauth_state'])
    
    def test_auth_callback_requires_valid_state(self):
        """Test that OAuth callback validates state parameter"""
        # Test with missing state
        response = self.client.get('/auth/callback')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with invalid state
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'
        
        response = self.client.get('/auth/callback?state=invalid-state')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @patch('app.google.authorize_access_token')
    def test_auth_callback_handles_oauth_errors(self, mock_authorize):
        """Test that OAuth callback handles errors gracefully"""
        # Set up valid state
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'test-state'
        
        # Mock OAuth failure
        mock_authorize.side_effect = Exception("OAuth error")
        
        response = self.client.get('/auth/callback?state=test-state')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_logout_route_clears_session(self):
        """Test that logout route clears user session"""
        # This test would need a logged-in user, which requires more complex mocking
        # For now, test that the route exists and redirects unauthenticated users
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)  # Redirect to login (unauthenticated)
    
    def test_protected_routes_require_authentication(self):
        """Test that protected routes redirect unauthenticated users"""
        protected_routes = ['/']
        
        for route in protected_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)  # Redirect to login


class TestOAuthIntegration(unittest.TestCase):
    """Integration tests for OAuth flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock environment variables
        os.environ.update({
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'HOSTED_DOMAIN': 'go.buu.ac.th',
            'FLASK_SECRET_KEY': 'test-secret-key'
        })
    
    @patch('app.login_user')
    @patch('app.employee_repo.create_or_update')
    @patch('app.google.authorize_access_token')
    def test_successful_oauth_flow_with_valid_domain(self, mock_authorize, mock_create_employee, mock_login):
        """Test complete OAuth flow with valid company domain"""
        # Set up valid state
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'test-state'
        
        # Mock successful OAuth response
        mock_token = {
            'userinfo': {
                'sub': 'google-user-id-123',
                'email': 'john.doe@go.buu.ac.th',
                'name': 'John Doe',
                'picture': 'https://example.com/photo.jpg'
            }
        }
        mock_authorize.return_value = mock_token
        
        # Mock employee creation - create a simple dict instead of MagicMock
        mock_employee = type('Employee', (), {
            'id': 1,
            'name': 'John Doe',
            'email': 'john.doe@go.buu.ac.th'
        })()
        mock_create_employee.return_value = mock_employee
        
        # Test OAuth callback
        response = self.client.get('/auth/callback?state=test-state')
        
        # Verify redirect to main page
        self.assertEqual(response.status_code, 302)
        
        # Verify employee creation was called
        mock_create_employee.assert_called_once_with(mock_token['userinfo'])
        
        # Verify login_user was called
        mock_login.assert_called_once_with(mock_employee, remember=True)
    
    @patch('app.google.authorize_access_token')
    def test_oauth_flow_rejects_invalid_domain(self, mock_authorize):
        """Test OAuth flow rejects users from invalid domains"""
        # Set up valid state
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'test-state'
        
        # Mock OAuth response with invalid domain
        mock_token = {
            'userinfo': {
                'sub': 'google-user-id-123',
                'email': 'john.doe@gmail.com',  # Invalid domain
                'name': 'John Doe',
                'picture': 'https://example.com/photo.jpg'
            }
        }
        mock_authorize.return_value = mock_token
        
        # Test OAuth callback
        response = self.client.get('/auth/callback?state=test-state')
        
        # Verify redirect to login page (rejection)
        self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    unittest.main()