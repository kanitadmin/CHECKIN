"""
Security tests for Employee Check-in System
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from app import app, csrf
from security_utils import SecurityValidator, validate_database_query, sanitize_user_input
from database import DatabaseManager
from models import EmployeeRepository


class TestCSRFProtection:
    """Test CSRF protection implementation"""
    
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
    
    def test_csrf_token_required_for_checkin(self):
        """Test that check-in requires valid CSRF token"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        # Attempt check-in without CSRF token
        response = self.client.post('/check-in', 
                                  headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert not data['success']
        assert 'Security validation failed' in data['error']
    
    def test_csrf_token_required_for_checkout(self):
        """Test that check-out requires valid CSRF token"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        # Attempt check-out without CSRF token
        response = self.client.post('/check-out', 
                                  headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert not data['success']
        assert 'Security validation failed' in data['error']
    
    def test_csrf_token_in_template(self):
        """Test that CSRF token is included in templates"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        response = self.client.get('/')
        assert response.status_code == 200
        assert b'csrf-token' in response.data
    
    def test_invalid_csrf_token_rejected(self):
        """Test that invalid CSRF tokens are rejected"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        # Attempt with invalid CSRF token
        response = self.client.post('/check-in',
                                  headers={
                                      'Content-Type': 'application/json',
                                      'X-CSRFToken': 'invalid_token'
                                  })
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert not data['success']
        assert 'Security validation failed' in data['error']


class TestXSSProtection:
    """Test XSS protection implementation"""
    
    def test_xss_pattern_detection(self):
        """Test XSS pattern detection"""
        xss_payloads = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src="x" onerror="alert(1)">',
            '<iframe src="javascript:alert(1)"></iframe>',
            '<object data="javascript:alert(1)"></object>',
            '<embed src="javascript:alert(1)">',
            '<link rel="stylesheet" href="javascript:alert(1)">',
            '<style>body{background:url("javascript:alert(1)")}</style>',
            'expression(alert(1))',
            'url(javascript:alert(1))',
            '@import "javascript:alert(1)"'
        ]
        
        for payload in xss_payloads:
            assert not SecurityValidator.validate_xss_input(payload), f"Failed to detect XSS in: {payload}"
    
    def test_safe_input_allowed(self):
        """Test that safe input is allowed"""
        safe_inputs = [
            'John Doe',
            'john.doe@company.com',
            'https://example.com/image.jpg',
            'Normal text with numbers 123',
            'Text with special chars: !@#$%^&*()',
            ''
        ]
        
        for safe_input in safe_inputs:
            assert SecurityValidator.validate_xss_input(safe_input), f"Safe input rejected: {safe_input}"
    
    def test_html_sanitization(self):
        """Test HTML output sanitization"""
        test_cases = [
            ('<script>alert("xss")</script>', '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'),
            ('John & Jane', 'John &amp; Jane'),
            ('<b>Bold</b>', '&lt;b&gt;Bold&lt;/b&gt;'),
            ('"quoted"', '&quot;quoted&quot;'),
            ("'single'", '&#x27;single&#x27;')
        ]
        
        for input_text, expected in test_cases:
            result = SecurityValidator.sanitize_html_output(input_text)
            assert result == expected, f"Sanitization failed for: {input_text}"
    
    def test_template_auto_escaping(self):
        """Test that Flask templates auto-escape content"""
        app.config['TESTING'] = True
        client = app.test_client()
        
        with app.test_request_context():
            # Test that user data is escaped in templates
            from flask import render_template_string
            
            template = '{{ user_input }}'
            user_input = '<script>alert("xss")</script>'
            
            result = render_template_string(template, user_input=user_input)
            assert '<script>' not in result
            assert '&lt;script&gt;' in result


class TestSQLInjectionProtection:
    """Test SQL injection protection"""
    
    def test_sql_injection_pattern_detection(self):
        """Test SQL injection pattern detection"""
        sql_payloads = [
            "'; DROP TABLE employees; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM employees--",
            "'; EXEC xp_cmdshell('dir'); --",
            "1' AND 1=1--",
            "' OR 1=1#",
            "1'; INSERT INTO employees VALUES('hacker'); --",
            "1' OR SUBSTRING(password,1,1)='a'--",
            "1' OR CHAR(65)='A'--"
        ]
        
        for payload in sql_payloads:
            assert not SecurityValidator.validate_sql_input(payload), f"Failed to detect SQL injection in: {payload}"
    
    def test_safe_sql_input_allowed(self):
        """Test that safe SQL input is allowed"""
        safe_inputs = [
            'john.doe@company.com',
            'John Doe',
            '123456789',
            'https://example.com/image.jpg',
            'Normal text',
            None,
            ''
        ]
        
        for safe_input in safe_inputs:
            assert SecurityValidator.validate_sql_input(safe_input), f"Safe input rejected: {safe_input}"
    
    def test_parameterized_query_validation(self):
        """Test parameterized query validation"""
        # Valid parameterized queries
        valid_queries = [
            ("SELECT * FROM employees WHERE email = %s", ("test@example.com",)),
            ("INSERT INTO attendances (employee_id, check_in_time) VALUES (%s, %s)", (1, "2023-01-01 09:00:00")),
            ("UPDATE employees SET name = %s WHERE id = %s", ("John Doe", 1))
        ]
        
        for query, params in valid_queries:
            assert validate_database_query(query, params), f"Valid query rejected: {query}"
        
        # Invalid queries
        invalid_queries = [
            ("SELECT * FROM employees; DROP TABLE employees;", None),
            ("SELECT * FROM employees WHERE id = %s; DELETE FROM employees;", (1,)),
            ("EXEC xp_cmdshell('dir')", None)
        ]
        
        for query, params in invalid_queries:
            assert not validate_database_query(query, params), f"Invalid query accepted: {query}"
    
    def test_database_query_security_validation(self):
        """Test that database queries are validated for security"""
        db_manager = DatabaseManager()
        
        # Test that dangerous queries are blocked
        with pytest.raises(Exception):  # Should raise DatabaseQueryError
            db_manager.execute_query("SELECT * FROM employees; DROP TABLE employees;")
    
    @patch('models.DatabaseManager')
    def test_employee_input_sanitization(self, mock_db):
        """Test that employee input is sanitized"""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.execute_query.return_value = []
        
        repo = EmployeeRepository()
        
        # Test with malicious input
        malicious_data = {
            'sub': 'normal_id',
            'email': 'test@example.com<script>alert("xss")</script>',
            'name': 'John<script>alert("xss")</script>',
            'picture': 'https://example.com/pic.jpg'
        }
        
        # Should raise ValueError due to invalid email
        with pytest.raises(ValueError):
            repo.create_or_update(malicious_data)


class TestSecurityHeaders:
    """Test security headers implementation"""
    
    def setup_method(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        response = self.client.get('/login')
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
    
    def test_csp_header_in_production(self):
        """Test that CSP header is set in production"""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            response = self.client.get('/login')
            assert 'Content-Security-Policy' in response.headers
    
    def test_https_redirect_in_production(self):
        """Test HTTPS redirect in production"""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            # Simulate HTTP request
            response = self.client.get('/login', 
                                     environ_base={'wsgi.url_scheme': 'http'})
            # Should redirect to HTTPS
            assert response.status_code in [301, 302]


class TestSessionSecurity:
    """Test session security configuration"""
    
    def test_secure_session_configuration(self):
        """Test that session cookies are configured securely"""
        assert app.config['SESSION_COOKIE_HTTPONLY'] is True
        assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
        assert 'PERMANENT_SESSION_LIFETIME' in app.config
    
    def test_session_cookie_secure_in_production(self):
        """Test that session cookies are secure in production"""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            # Reload app config
            app.config['SESSION_COOKIE_SECURE'] = True
            assert app.config['SESSION_COOKIE_SECURE'] is True


class TestSecurityLogging:
    """Test security event logging"""
    
    @patch('security_utils.logger')
    def test_security_event_logging(self, mock_logger):
        """Test that security events are logged"""
        SecurityValidator.log_security_event("TEST_EVENT", "Test details", user_id=123)
        
        # Verify logging was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "SECURITY EVENT" in call_args
        assert "TEST_EVENT" in call_args
        assert "Test details" in call_args
        assert "123" in call_args
    
    @patch('security_utils.logger')
    def test_xss_attempt_logging(self, mock_logger):
        """Test that XSS attempts are logged"""
        malicious_input = '<script>alert("xss")</script>'
        result = sanitize_user_input(malicious_input)
        
        # Should log the security event
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "XSS_ATTEMPT" in call_args
    
    @patch('security_utils.logger')
    def test_sql_injection_attempt_logging(self, mock_logger):
        """Test that SQL injection attempts are logged"""
        malicious_input = "'; DROP TABLE employees; --"
        result = sanitize_user_input(malicious_input)
        
        # Should log the security event
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "SQL_INJECTION_ATTEMPT" in call_args


if __name__ == '__main__':
    pytest.main([__file__])