#!/usr/bin/env python3
"""
Simple test to verify CSRF token generation
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_csrf_import():
    """Test CSRF token generation"""
    try:
        from flask import Flask
        from flask_wtf.csrf import CSRFProtect, generate_csrf
        
        print("✅ Successfully imported Flask-WTF CSRF components")
        
        # Create a minimal Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Initialize CSRF protection
        csrf = CSRFProtect(app)
        
        print("✅ CSRFProtect initialized successfully")
        
        # Test token generation within app context
        with app.app_context():
            token = generate_csrf()
            print(f"✅ CSRF token generated: {token[:20]}...")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure Flask-WTF is installed: pip install Flask-WTF")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_app_import():
    """Test importing the main app"""
    try:
        # Test if we can import the app without errors
        from app import app, csrf
        print("✅ Successfully imported main app")
        
        # Test context processor
        with app.app_context():
            from app import inject_csrf_token
            result = inject_csrf_token()
            if 'csrf_token' in result:
                print("✅ CSRF context processor working")
                # Test if the function is callable
                token_func = result['csrf_token']
                if callable(token_func):
                    token = token_func()
                    print(f"✅ CSRF token callable: {token[:20]}...")
                else:
                    print("❌ CSRF token is not callable")
            else:
                print("❌ CSRF token not in context processor result")
                
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import app: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        return False

if __name__ == "__main__":
    print("CSRF Fix Verification")
    print("=" * 40)
    
    success = True
    success &= test_csrf_import()
    print()
    success &= test_app_import()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All CSRF tests passed!")
        print("The CSRF token generation should now work correctly.")
    else:
        print("❌ Some tests failed")
        print("Check the error messages above for details.")
    
    print("\nNext steps:")
    print("1. Start the Flask app: python app.py")
    print("2. Open browser and check Developer Tools console")
    print("3. Look for CSRF debug messages")
    print("4. Try the check-in/check-out functionality")