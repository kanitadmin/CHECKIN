#!/usr/bin/env python3
"""
Test script to verify the system works without CSRF protection
"""

import requests
import json

def test_no_csrf():
    """Test if the system works without CSRF protection"""
    
    print("🧪 Testing System Without CSRF Protection")
    print("=" * 50)
    
    try:
        # Test 1: Check if login page loads
        print("1. Testing login page...")
        response = requests.get('http://localhost:5000/login', timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Login page loads successfully")
            
            # Check that CSRF meta tag is NOT present
            if 'csrf-token' not in response.text:
                print("   ✅ CSRF meta tag removed successfully")
            else:
                print("   ⚠️  CSRF meta tag still present (may need manual cleanup)")
        else:
            print(f"   ❌ Login page returned status: {response.status_code}")
            return False
            
        # Test 2: Check if check-in endpoint is accessible (should require auth)
        print("\n2. Testing check-in endpoint...")
        response = requests.post('http://localhost:5000/check-in', 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 401:
            print("   ✅ Check-in endpoint properly requires authentication")
        elif response.status_code == 403:
            print("   ❌ Check-in endpoint still has CSRF protection")
            return False
        else:
            print(f"   ℹ️  Check-in endpoint returned: {response.status_code}")
            
        # Test 3: Check if check-out endpoint is accessible (should require auth)
        print("\n3. Testing check-out endpoint...")
        response = requests.post('http://localhost:5000/check-out', 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 401:
            print("   ✅ Check-out endpoint properly requires authentication")
        elif response.status_code == 403:
            print("   ❌ Check-out endpoint still has CSRF protection")
            return False
        else:
            print(f"   ℹ️  Check-out endpoint returned: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to http://localhost:5000")
        print("   💡 Make sure the Flask app is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def show_next_steps():
    """Show next steps for testing"""
    
    print("\n📋 Next Steps for Testing")
    print("=" * 50)
    print("1. Start the Flask app:")
    print("   python app.py")
    print()
    print("2. Open browser and go to: http://localhost:5000")
    print()
    print("3. Log in with your Google account")
    print()
    print("4. Try the check-in and check-out buttons")
    print("   - Should work without 'Security validation failed' error")
    print()
    print("5. Check browser console (F12) for any JavaScript errors")
    print()
    print("6. If you see any CSRF-related errors:")
    print("   - Restart the Flask app")
    print("   - Clear browser cache and cookies")
    print("   - Try in incognito/private mode")
    print()

if __name__ == "__main__":
    success = test_no_csrf()
    
    if success:
        print("\n🎉 CSRF Removal Successful!")
        print("The system should now work without CSRF protection.")
        print("The 'Security validation failed' error should be resolved.")
    else:
        print("\n⚠️  CSRF Removal Needs Attention")
        print("Please check the Flask app and try again.")
    
    show_next_steps()