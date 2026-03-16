"""
Setup script to create initial admin user
"""
import os
import sys
from getpass import getpass
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import Admin

load_dotenv()

def create_admin():
    """Create a new admin user"""
    with app.app_context():
        print("\n" + "="*50)
        print("CREATE ADMIN USER")
        print("="*50 + "\n")
        
        username = input("Enter admin username: ").strip()
        email = input("Enter admin email: ").strip()
        full_name = input("Enter full name: ").strip()
        
        # Check if admin already exists
        if Admin.query.filter_by(username=username).first():
            print(f"\n❌ Admin with username '{username}' already exists!")
            return
        
        if Admin.query.filter_by(email=email).first():
            print(f"\n❌ Admin with email '{email}' already exists!")
            return
        
        # Get password
        while True:
            password = getpass("Enter password (min 6 characters): ")
            if len(password) < 6:
                print("❌ Password must be at least 6 characters!")
                continue
            
            confirm = getpass("Confirm password: ")
            if password != confirm:
                print("❌ Passwords don't match!")
                continue
            
            break
        
        # Create admin
        admin = Admin()
        admin.username = username
        admin.email = email
        admin.full_name = full_name
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Full Name: {full_name}")
        print("\nYou can now login at /admin/login\n")

if __name__ == '__main__':
    create_admin()
