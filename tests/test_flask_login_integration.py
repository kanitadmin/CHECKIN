"""
Test Flask-Login integration with Employee model
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from app import app, load_user
from models import Employee


class TestFlaskLoginIntegration(unittest.TestCase):
    """Test Flask-Login integration with Employee model"""
    
    def setUp(self):
        """Set up test fixtures"""
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
        
        # Sample employee data
        self.sample_employee = Employee(
            id=1,
            google_id='google_123456789',
            email='test@go.buu.ac.th',
            name='Test User',
            picture_url='https://example.com/pic.jpg'
        )
    
    @patch('app.employee_repo')
    def test_load_user_success(self, mock_repo):
        """Test successful user loading by Flask-Login"""
        # Setup mock
        mock_repo.find_by_id.return_value = self.sample_employee
        
        # Test load_user function
        result = load_user('1')
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.email, 'test@go.buu.ac.th')
        mock_repo.find_by_id.assert_called_once_with(1)
    
    @patch('app.employee_repo')
    def test_load_user_not_found(self, mock_repo):
        """Test user loading when employee not found"""
        # Setup mock
        mock_repo.find_by_id.return_value = None
        
        # Test load_user function
        result = load_user('999')
        
        # Verify
        self.assertIsNone(result)
        mock_repo.find_by_id.assert_called_once_with(999)
    
    @patch('app.employee_repo')
    def test_load_user_invalid_id(self, mock_repo):
        """Test user loading with invalid user ID"""
        # Test with non-numeric ID
        result = load_user('invalid')
        
        # Verify
        self.assertIsNone(result)
        mock_repo.find_by_id.assert_not_called()
        
        # Test with None
        result = load_user(None)
        
        # Verify
        self.assertIsNone(result)
        mock_repo.find_by_id.assert_not_called()
    
    def test_employee_flask_login_methods(self):
        """Test Employee class Flask-Login UserMixin methods"""
        # Test all required Flask-Login methods
        self.assertEqual(self.sample_employee.get_id(), '1')
        self.assertTrue(self.sample_employee.is_authenticated)
        self.assertTrue(self.sample_employee.is_active)
        self.assertFalse(self.sample_employee.is_anonymous)
    
    def test_flask_app_configuration(self):
        """Test Flask app has proper Flask-Login configuration"""
        with self.app.app_context():
            # Check that login manager is configured
            self.assertIsNotNone(app.login_manager)
            self.assertEqual(app.login_manager.login_view, 'login')


class TestAuthenticationFlowIntegration(unittest.TestCase):
    """Integration tests for complete authentication flow from login to session creation"""
    
    def setUp(self):
        """Set up test environment"""
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
    
    @patch('app.login_user')
    @patch('app.employee_repo.create_or_update')
    @patch('app.google.authorize_access_token')
    def test_complete_authentication_flow_success(self, mock_authorize, mock_create_employee, mock_login):
        """Test complete authentication flow from OAuth callback to session creation"""
        # Set up valid state in session
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'test-state-123'
        
        # Mock successful OAuth response with valid company domain
        mock_token = {
            'userinfo': {
                'sub': 'google-user-id-123',
                'email': 'john.doe@go.buu.ac.th',
                'name': 'John Doe',
                'picture': 'https://example.com/photo.jpg'
            }
        }
        mock_authorize.return_value = mock_token
        
        # Mock employee creation/update
        mock_employee = Employee(
            id=1,
            google_id='google-user-id-123',
            email='john.doe@go.buu.ac.th',
            name='John Doe',
            picture_url='https://example.com/photo.jpg'
        )
        mock_create_employee.return_value = mock_employee
        
        # Execute OAuth callback
        response = self.client.get('/auth/callback?state=test-state-123')
        
        # Verify successful redirect to main dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))
        
        # Verify employee repository was called with correct data
        mock_create_employee.assert_called_once_with(mock_token['userinfo'])
        
        # Verify Flask-Login session was created
        mock_login.assert_called_once_with(mock_employee, remember=True)
        
        # Verify OAuth state was cleared from session
        with self.client.session_transaction() as sess:
            self.assertNotIn('oauth_state', sess)
    
    @patch('app.google.authorize_access_token')
    def test_authentication_flow_domain_validation_failure(self, mock_authorize):
        """Test authentication flow fails with invalid domain and redirects to login"""
        # Set up valid state in session
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'test-state-123'
        
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
        
        # Execute OAuth callback
        response = self.client.get('/auth/callback?state=test-state-123')
        
        # Verify redirect to login page due to domain validation failure
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/login'))
    
    def test_authentication_flow_csrf_protection(self):
        """Test authentication flow CSRF protection with invalid state parameter"""
        # Set up valid state in session
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'
        
        # Try callback with different state (CSRF attack simulation)
        response = self.client.get('/auth/callback?state=invalid-state')
        
        # Verify redirect to login page due to CSRF protection
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/login'))
    
    @patch('app.employee_repo.create_or_update')
    @patch('app.google.authorize_access_token')
    def test_authentication_flow_employee_creation_failure(self, mock_authorize, mock_create_employee):
        """Test authentication flow handles employee creation failure gracefully"""
        # Set up valid state in session
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'test-state-123'
        
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
        
        # Mock employee creation failure
        mock_create_employee.return_value = None
        
        # Execute OAuth callback
        response = self.client.get('/auth/callback?state=test-state-123')
        
        # Verify redirect to login page due to employee creation failure
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/login'))
    
    @patch('app.logout_user')
    def test_logout_flow_clears_session(self, mock_logout):
        """Test logout flow clears Flask-Login session and redirects to login"""
        # Mock authenticated user for logout test
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_user = Employee(
                id=1,
                google_id='google-123',
                email='test@go.buu.ac.th',
                name='Test User'
            )
            mock_get_user.return_value = mock_user
            
            # Execute logout
            response = self.client.get('/logout')
            
            # Verify logout_user was called
            mock_logout.assert_called_once()
            
            # Verify redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/login'))
    
    def test_login_required_decorator_redirects_unauthenticated_users(self):
        """Test that login_required decorator properly redirects unauthenticated users"""
        # Test accessing protected route without authentication
        response = self.client.get('/')
        
        # Verify redirect to login page
        self.assertEqual(response.status_code, 302)
        # Check if redirect contains login in the path
        self.assertIn('login', response.location)
    
    def test_authenticated_user_can_access_protected_routes(self):
        """Test that authenticated users can access protected routes"""
        # This test verifies the login_required decorator works correctly
        # We'll test this by simulating a login session
        with self.client.session_transaction() as sess:
            # Simulate Flask-Login session data
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        # Mock the user loader to return a valid user
        with patch('app.employee_repo.find_by_id') as mock_find:
            mock_user = Employee(
                id=1,
                google_id='google-123',
                email='test@go.buu.ac.th',
                name='Test User'
            )
            mock_find.return_value = mock_user
            
            # Test accessing protected route with authentication
            response = self.client.get('/')
            
            # Verify successful access (not a redirect)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test User', response.data)
    
    @patch('app.google.authorize_redirect')
    def test_oauth_state_generation_and_storage(self, mock_authorize):
        """Test that OAuth state parameter is properly generated and stored"""
        # Mock the OAuth redirect to avoid network calls
        mock_authorize.return_value = 'mocked_redirect_response'
        
        # Initiate OAuth flow
        response = self.client.get('/auth/google')
        
        # Verify state parameter was stored in session
        with self.client.session_transaction() as sess:
            self.assertIn('oauth_state', sess)
            self.assertIsNotNone(sess['oauth_state'])
            self.assertGreater(len(sess['oauth_state']), 20)  # Should be a substantial random string
        
        # Verify authorize_redirect was called
        mock_authorize.assert_called_once()


if __name__ == '__main__':
    unittest.main()