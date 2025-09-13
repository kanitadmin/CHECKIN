#!/usr/bin/env python3
"""
Quick test to verify the CSRF fix
Run this after starting the Flask app
"""

import requests
import re

def test_csrf_fix():
    """Test if CSRF token is now working"""
    
    print("🧪 Testing CSRF Token Fix")
    print("=" * 40)
    
    try:
        # Test the login page (should be accessible)
        print("1. Testing login page access...")
        response = requests.get('http://localhost:5000/login', timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Login page accessible")
            
            # Check for CSRF token in HTML
            if 'csrf-token' in response.text:
                print("   ✅ CSRF meta tag found in HTML")
                
                # Extract token
                token_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
                if token_match:
                    token = token_match.group(1)
                    if token and len(token) > 10:  # Valid token should be longer
                        print(f"   ✅ Valid CSRF token extracted: {token[:20]}...")
                        return True
                    else:
                        print("   ❌ CSRF token is empty or too short")
                else:
                    print("   ❌ Could not extract CSRF token from meta tag")
            else:
                print("   ❌ CSRF meta tag not found in HTML")
        else:
            print(f"   ❌ Login page returned status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to http://localhost:5000")
        print("   💡 Make sure the Flask app is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return False

def show_instructions():
    """Show instructions for manual testing"""
    
    print("\n📋 Manual Testing Instructions")
    print("=" * 40)
    print("1. Start the Flask app:")
    print("   python app.py")
    print()
    print("2. Open browser and go to: http://localhost:5000")
    print()
    print("3. Open Developer Tools (F12) and check Console")
    print()
    print("4. Look for CSRF debug messages:")
    print("   - Should see: '🔍 CSRF Debug Helper loaded'")
    print("   - Should see: '✅ CSRF token found in meta tag'")
    print()
    print("5. Try logging in and using check-in/check-out")
    print()
    print("6. If still having issues, run in Console:")
    print("   window.csrfDebug.show()")
    print()

if __name__ == "__main__":
    success = test_csrf_fix()
    
    if success:
        print("\n🎉 CSRF Fix Successful!")
        print("The 'Security validation failed' error should be resolved.")
    else:
        print("\n⚠️  CSRF Fix Needs Attention")
        print("Please check the Flask app configuration.")
    
    show_instructions()