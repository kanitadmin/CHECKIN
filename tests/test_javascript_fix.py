#!/usr/bin/env python3
"""
Test script to verify JavaScript fix for admin locations page
"""

import requests
import re

def test_javascript_loading():
    """Test if JavaScript is properly loaded in admin locations page"""
    
    print("🧪 Testing JavaScript Loading Fix")
    print("=" * 50)
    
    try:
        # Test admin locations page
        print("1. Testing admin locations page...")
        response = requests.get('http://localhost:5000/admin/locations', timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Admin locations page accessible")
            
            # Check for JavaScript function
            if 'openAddLocationModal' in response.text:
                print("   ✅ openAddLocationModal function found in HTML")
            else:
                print("   ❌ openAddLocationModal function not found in HTML")
                
            # Check for modal HTML
            if 'id="locationModal"' in response.text:
                print("   ✅ Location modal HTML found")
            else:
                print("   ❌ Location modal HTML not found")
                
            # Check for admin_extra_js block
            if '<script>' in response.text and 'openAddLocationModal' in response.text:
                print("   ✅ JavaScript appears to be properly embedded")
            else:
                print("   ❌ JavaScript may not be properly embedded")
                
            # Check for button with onclick
            if 'onclick="openAddLocationModal()"' in response.text:
                print("   ✅ Button with onclick handler found")
            else:
                print("   ❌ Button with onclick handler not found")
                
        elif response.status_code == 302:
            print("   ℹ️  Redirected (login required)")
        else:
            print(f"   ❌ Admin locations page returned status: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to http://localhost:5000")
        print("   💡 Make sure the Flask app is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def show_test_instructions():
    """Show manual testing instructions"""
    
    print("\n📋 Manual Testing Instructions")
    print("=" * 50)
    print("1. Open browser and go to:")
    print("   http://localhost:5000/admin/locations")
    print()
    print("2. Open Developer Tools (F12)")
    print("   - Go to Console tab")
    print("   - Look for any JavaScript errors")
    print()
    print("3. Test JavaScript function:")
    print("   - In Console, type: typeof openAddLocationModal")
    print("   - Should return: 'function'")
    print()
    print("4. Test modal opening:")
    print("   - In Console, type: openAddLocationModal()")
    print("   - Modal should open")
    print()
    print("5. Test button click:")
    print("   - Click 'เพิ่มตำแหน่งใหม่' button")
    print("   - Modal should open")
    print()
    print("6. If still not working:")
    print("   - Hard refresh: Ctrl+F5")
    print("   - Clear cache: Ctrl+Shift+Delete")
    print("   - Try incognito mode: Ctrl+Shift+N")
    print()

def show_fix_summary():
    """Show summary of the fix applied"""
    
    print("\n🔧 Fix Applied")
    print("=" * 50)
    print("Problem: JavaScript function 'openAddLocationModal' not defined")
    print()
    print("Root Cause:")
    print("- admin_extra_js block was not inside extra_js block")
    print("- JavaScript was not being rendered to the page")
    print()
    print("Solution:")
    print("- Moved admin_extra_js block inside extra_js block in admin_layout.html")
    print("- Now JavaScript is properly inherited from layout.html")
    print()
    print("Template Structure (Fixed):")
    print("layout.html")
    print("├── extra_js block")
    print("    └── admin_layout.html")
    print("        └── admin_extra_js block")
    print("            └── locations.html")
    print("                └── JavaScript functions")
    print()

if __name__ == "__main__":
    success = test_javascript_loading()
    
    if success:
        print("\n🎉 JavaScript Loading Test Completed!")
    else:
        print("\n⚠️  JavaScript Loading Test Failed")
    
    show_fix_summary()
    show_test_instructions()
    
    print("\n💡 Expected Results After Fix:")
    print("- No 'ReferenceError: openAddLocationModal is not defined'")
    print("- Button 'เพิ่มตำแหน่งใหม่' should work")
    print("- Modal should open when button is clicked")
    print("- JavaScript functions should be available in Console")