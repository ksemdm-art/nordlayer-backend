#!/usr/bin/env python3
"""
Script to create the first admin user.
Usage: python -m app.scripts.create_admin
"""

import sys
from getpass import getpass
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate

def create_admin_user():
    """Create admin user interactively."""
    print("Creating admin user...")
    
    # Get user input
    username = input("Username: ").strip()
    if not username:
        print("Username is required")
        return False
    
    email = input("Email: ").strip()
    if not email:
        print("Email is required")
        return False
    
    full_name = input("Full name (optional): ").strip() or None
    
    password = getpass("Password: ")
    if not password:
        print("Password is required")
        return False
    
    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("Passwords do not match")
        return False
    
    # Create user
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = user_crud.get_by_email(db, email=email)
        if existing_user:
            print(f"User with email {email} already exists")
            return False
        
        existing_username = user_crud.get_by_username(db, username=username)
        if existing_username:
            print(f"User with username {username} already exists")
            return False
        
        # Create admin user
        user_in = UserCreate(
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            is_admin=True,
            is_active=True
        )
        
        user = user_crud.create(db, obj_in=user_in)
        print(f"Admin user created successfully: {user.username} ({user.email})")
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function."""
    if not create_admin_user():
        sys.exit(1)

if __name__ == "__main__":
    main()