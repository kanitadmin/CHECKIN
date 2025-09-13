#!/usr/bin/env python3
"""
Test script to verify CSRF token functionality
"""

import requests
import re
from bs4 import BeautifulSoup

def test_csrf_token():
    """Test CSRF token generation and validation"""
    
    # Test 1: Check if CSRF token is present in the page
    print("Testing CSRF token presence...")
    
    try:
        # Make a request to the login page (should be accessible without auth)
        response = requests.get('http://localhost:5000/login')
        
        if response.status_code == 200:
            # Check if meta tag with csrf-token exists
            if 'csrf-token' in response.text:
                print("✓ CSRF token meta tag found in HTML")
                
                # Extract token using regex
                token_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
                if token_match:
                    token = token_match.group(1)
                    print(f"✓ CSRF token extracted: {token[:20]}...")
                else:
                    print("✗ Could not extract CSRF token from meta tag")
            else:
                print("✗ CSRF token meta tag not found")
        else:
            print(f"✗ Could not access login page: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the app is running on localhost:5000")
        return False
    except Exception as e:
        print(f"✗ Error testing CSRF token: {e}")
        return False
    
    return True

def test_csrf_validation():
    """Test CSRF validation on protected endpoints"""
    
    print("\nTesting CSRF validation...")
    
    try:
        # Test check-in endpoint without CSRF token
        response = requests.post('http://localhost:5000/check-in', 
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 401:
            print("✓ Check-in endpoint properly rejects requests without authentication")
        elif response.status_code == 403:
            print("✓ Check-in endpoint properly rejects requests without CSRF token")
        else:
            print(f"? Check-in endpoint returned: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server")
        return False
    except Exception as e:
        print(f"✗ Error testing CSRF validation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("CSRF Token Test Script")
    print("=" * 40)
    
    success = True
    success &= test_csrf_token()
    success &= test_csrf_validation()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests completed")
    else:
        print("✗ Some tests failed")
    
    print("\nTo fix CSRF issues:")
    print("1. Make sure Flask-WTF is properly configured")
    print("2. Check that csrf_token() function is available in templates")
    print("3. Verify JavaScript is sending X-CSRFToken header")
    print("4. Check browser developer tools for any JavaScript errors")