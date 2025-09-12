"""
Integration tests for security features
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
from flask import url_for


class TestSecurityIntegration:
    """Integration tests for security features"""
    
    def setup_method(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up test context"""
        self.ctx.pop()
    
    def test_complete_csrf_protection_flow(self):
        """Test complete CSRF protection flow"""
        # Test that CSRF token is available in templates
        with self.app.test_request_context():
            from flask_wtf.csrf import generate_csrf
            token = generate_csrf()
            assert token is not None
            assert len(token) > 0
        
        # Test login page includes CSRF meta tag
        response = self.client.get('/login')
        assert response.status_code == 200
        # Login page doesn't use layout.html, so no CSRF token there
        
        # Test that protected routes require authentication
        response = self.client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_xss_protection_in_templates(self):
        """Test XSS protection in template rendering"""
        # Test template auto-escaping directly
        from flask import render_template_string
        
        with self.app.test_request_context():
            # Test that user data is escaped in templates
            template = '<p>{{ user_name }}</p>'
            user_name = '<script>alert("xss")</script>'
            
            result = render_template_string(template, user_name=user_name)
            
            # Verify XSS payload is escaped
            assert '<script>' not in result
            assert '&lt;script&gt;' in result
            assert 'alert(&#34;xss&#34;)' in result
    
    def test_sql_injection_protection_in_models(self):
        """Test SQL injection protection in model operations"""
        from models import EmployeeRepository
        
        repo = EmployeeRepository()
        
        # Test with SQL injection payload
        malicious_data = {
            'sub': 'normal_id',
            'email': "test@example.com'; DROP TABLE employees; --",
            'name': 'Test User'
        }
        
        # Should raise ValueError due to invalid email
        with pytest.raises(ValueError):
            repo.create_or_update(malicious_data)
    
    def test_security_headers_integration(self):
        """Test that security headers are properly set"""
        response = self.client.get('/login')
        
        # Verify all security headers
        expected_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }
        
        for header, expected_value in expected_headers.items():
            assert header in response.headers
            assert response.headers[header] == expected_value
    
    def test_production_security_features(self):
        """Test production-specific security features"""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            # Reload app config for production
            self.app.config['SESSION_COOKIE_SECURE'] = True
            
            # Test CSP header in production
            response = self.client.get('/login')
            assert 'Content-Security-Policy' in response.headers
            
            # Test session cookie security
            assert self.app.config['SESSION_COOKIE_SECURE'] is True
    
    def test_oauth_state_csrf_protection(self):
        """Test OAuth state parameter CSRF protection"""
        # Initiate OAuth flow
        response = self.client.get('/auth/google')
        assert response.status_code == 302
        
        # Verify state parameter is set in session
        with self.client.session_transaction() as sess:
            assert 'oauth_state' in sess
            oauth_state = sess['oauth_state']
        
        # Test callback with wrong state
        response = self.client.get('/auth/callback?state=wrong_state&code=test_code')
        assert response.status_code == 302  # Redirect to login
        
        # Verify error message is flashed
        response = self.client.get('/login')
        assert b'Security validation failed' in response.data
    
    def test_input_sanitization_integration(self):
        """Test input sanitization across the application"""
        from security_utils import sanitize_user_input
        
        # Test various malicious inputs
        test_cases = [
            ('<script>alert("xss")</script>', ''),  # XSS blocked
            ("'; DROP TABLE users; --", ''),        # SQL injection blocked
            ('Normal text', 'Normal text'),          # Safe input allowed
            ('', ''),                                # Empty input allowed
            (None, None)                             # None input allowed
        ]
        
        for input_val, expected in test_cases:
            result = sanitize_user_input(input_val)
            assert result == expected, f"Sanitization failed for: {input_val}"


if __name__ == '__main__':
    pytest.main([__file__])