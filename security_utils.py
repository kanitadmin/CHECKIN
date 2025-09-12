"""
Security utilities for Employee Check-in System
"""
import re
import logging
from typing import Any, List, Tuple, Optional
from flask import request
import html

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation utilities"""
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bOR\s+\w+\s*=\s*\w+)",
        r"(\'\s*(OR|AND)\s*\'\w*\'\s*=\s*\'\w*)",
        r"(\bUNION\s+(ALL\s+)?SELECT)",
        r"(\bEXEC\s*\()",
        r"(\bCHAR\s*\(\d+\))",
        r"(\bCONCAT\s*\()",
        r"(\bSUBSTRING\s*\()",
    ]
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"<style[^>]*>.*?</style>",
        r"expression\s*\(",
        r"url\s*\(",
        r"@import",
    ]
    
    @classmethod
    def validate_sql_input(cls, input_value: Any) -> bool:
        """
        Validate input for potential SQL injection attempts
        
        Args:
            input_value: Value to validate
            
        Returns:
            True if input appears safe, False if suspicious patterns detected
        """
        if input_value is None:
            return True
        
        # Convert to string for pattern matching
        str_value = str(input_value).upper()
        
        # Check against SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, str_value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern} in {input_value}")
                return False
        
        return True
    
    @classmethod
    def validate_xss_input(cls, input_value: str) -> bool:
        """
        Validate input for potential XSS attempts
        
        Args:
            input_value: String value to validate
            
        Returns:
            True if input appears safe, False if suspicious patterns detected
        """
        if not input_value:
            return True
        
        # Check against XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {pattern} in {input_value}")
                return False
        
        return True
    
    @classmethod
    def sanitize_html_output(cls, text: str) -> str:
        """
        Sanitize text for safe HTML output
        
        Args:
            text: Text to sanitize
            
        Returns:
            HTML-escaped text
        """
        if not text:
            return ""
        
        return html.escape(str(text))
    
    @classmethod
    def validate_query_parameters(cls, query: str, params: Optional[Tuple] = None) -> bool:
        """
        Validate SQL query and parameters for security
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            True if query appears safe, False otherwise
        """
        # Ensure query uses parameterized statements
        if params is None and ('%s' in query or '?' in query):
            logger.error("Query contains parameter placeholders but no parameters provided")
            return False
        
        # Check for dangerous SQL patterns in the query itself
        dangerous_patterns = [
            r";\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)",
            r"EXEC\s*\(",
            r"xp_cmdshell",
            r"sp_executesql",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.error(f"Dangerous SQL pattern detected in query: {pattern}")
                return False
        
        # Validate parameters if provided
        if params:
            for param in params:
                if not cls.validate_sql_input(param):
                    return False
        
        return True
    
    @classmethod
    def log_security_event(cls, event_type: str, details: str, user_id: Optional[int] = None):
        """
        Log security-related events
        
        Args:
            event_type: Type of security event
            details: Event details
            user_id: User ID if applicable
        """
        client_ip = request.remote_addr if request else 'unknown'
        user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
        
        logger.warning(
            f"SECURITY EVENT - Type: {event_type}, "
            f"Details: {details}, "
            f"User ID: {user_id}, "
            f"IP: {client_ip}, "
            f"User-Agent: {user_agent}"
        )


def validate_database_query(query: str, params: Optional[Tuple] = None) -> bool:
    """
    Decorator function to validate database queries
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        True if query is valid, False otherwise
    """
    return SecurityValidator.validate_query_parameters(query, params)


def sanitize_user_input(input_data: Any) -> Any:
    """
    Sanitize user input for safe processing
    
    Args:
        input_data: Input data to sanitize
        
    Returns:
        Sanitized input data
    """
    if isinstance(input_data, str):
        # Validate for XSS
        if not SecurityValidator.validate_xss_input(input_data):
            SecurityValidator.log_security_event("XSS_ATTEMPT", f"Blocked XSS attempt: {input_data}")
            return ""
        
        # Validate for SQL injection
        if not SecurityValidator.validate_sql_input(input_data):
            SecurityValidator.log_security_event("SQL_INJECTION_ATTEMPT", f"Blocked SQL injection attempt: {input_data}")
            return ""
        
        return input_data.strip()
    
    return input_data