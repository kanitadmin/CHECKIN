#!/usr/bin/env python3
"""
Test script to verify admin menu functionality
"""

import requests
import re

def test_admin_menu():
    """Test if admin menu is accessible and contains location management"""
    
    print("🧪 Testing Admin Menu")
    print("=" * 40)
    
    try:
        # Test admin dashboard
        print("1. Testing admin dashboard...")
        response = requests.get('http://localhost:5000/admin', timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Admin dashboard accessible")
            
            # Check for location menu
            if 'จัดการตำแหน่ง' in response.text:
                print("   ✅ Location management menu found")
            else:
                print("   ❌ Location management menu not found")
                
            # Check for admin layout
            if 'Admin Panel' in response.text:
                print("   ✅ Admin layout loaded correctly")
            else:
                print("   ❌ Admin layout not loaded")
                
        elif response.status_code == 302:
            print("   ℹ️  Redirected (login required)")
        else:
            print(f"   ❌ Admin dashboard returned status: {response.status_code}")
            
        # Test location management page
        print("\n2. Testing location management page...")
        response = requests.get('http://localhost:5000/admin/locations', timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Location management page accessible")
            
            # Check for key elements
            if 'เพิ่มตำแหน่งใหม่' in response.text:
                print("   ✅ Add location button found")
            else:
                print("   ❌ Add location button not found")
                
        elif response.status_code == 302:
            print("   ℹ️  Redirected (login required)")
        else:
            print(f"   ❌ Location page returned status: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to http://localhost:5000")
        print("   💡 Make sure the Flask app is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def show_navigation_guide():
    """Show step-by-step navigation guide"""
    
    print("\n📋 How to Access Location Management")
    print("=" * 40)
    print("1. Start the Flask app:")
    print("   python app.py")
    print()
    print("2. Open browser and go to:")
    print("   http://localhost:5000")
    print()
    print("3. Log in with your Google account")
    print()
    print("4. Make sure you have admin privileges")
    print("   (Check with: python create_admin.py)")
    print()
    print("5. Go to Admin Dashboard:")
    print("   http://localhost:5000/admin")
    print()
    print("6. Look for the sidebar menu on the left:")
    print("   📊 แดชบอร์ด")
    print("   👥 จัดการพนักงาน")
    print("   📍 จัดการตำแหน่ง  ← Click here!")
    print()
    print("7. Or go directly to:")
    print("   http://localhost:5000/admin/locations")
    print()
    print("8. Click 'เพิ่มตำแหน่งใหม่' to add a location")
    print()

if __name__ == "__main__":
    success = test_admin_menu()
    
    if success:
        print("\n🎉 Admin Menu Test Completed!")
    else:
        print("\n⚠️  Admin Menu Test Failed")
    
    show_navigation_guide()
    
    print("\n💡 Troubleshooting Tips:")
    print("- Make sure you're logged in as admin")
    print("- Check browser console (F12) for JavaScript errors")
    print("- Try refreshing the page")
    print("- Clear browser cache and cookies")