#!/usr/bin/env python3
"""
Script to create the first admin user
Run this after setting up your database and environment variables
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database, DatabaseManager
from models import EmployeeRepository

def create_admin_user():
    """Create the first admin user"""
    
    # Check if environment variables are set
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with database configuration.")
        return False
    
    try:
        print("🔧 Initializing database...")
        initialize_database()
        print("✅ Database initialized successfully")
        
        # Get admin email from user input
        admin_email = input("\n📧 Enter admin email address: ").strip()
        
        if not admin_email or '@' not in admin_email:
            print("❌ Invalid email address")
            return False
        
        # Check if user already exists
        employee_repo = EmployeeRepository()
        existing_user = employee_repo.find_by_email(admin_email)
        
        if existing_user:
            if existing_user.is_admin:
                print(f"✅ User {admin_email} is already an admin")
                return True
            else:
                # Update existing user to admin
                employee_repo.update_employee_role(existing_user.id, 'admin')
                print(f"✅ Updated {admin_email} to admin role")
                return True
        else:
            print(f"❌ User {admin_email} not found in database")
            print("The user must log in through Google OAuth at least once before being made an admin.")
            print("Please ask the user to:")
            print("1. Visit your application")
            print("2. Log in with Google OAuth")
            print("3. Then run this script again")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_users():
    """List all users in the system"""
    try:
        employee_repo = EmployeeRepository()
        employees = employee_repo.get_all_employees()
        
        if not employees:
            print("📭 No users found in the system")
            return
        
        print(f"\n👥 Found {len(employees)} users:")
        print("-" * 80)
        print(f"{'ID':<5} {'Email':<35} {'Name':<25} {'Role':<10}")
        print("-" * 80)
        
        for emp in employees:
            role = "Admin" if emp.is_admin else "Employee"
            name = emp.name or "No name"
            print(f"{emp.id:<5} {emp.email:<35} {name:<25} {role:<10}")
        
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")

def main():
    """Main function"""
    print("🚀 Employee Check-in System - Admin Setup")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Create/Update admin user")
        print("2. List all users")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            create_admin_user()
        elif choice == '2':
            list_users()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == '__main__':
    main()