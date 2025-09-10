#!/usr/bin/env python
"""
Script to create an initial admin user for Summerfest Registration System
Run this after setting up the database
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summerfest.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    """Create admin user if it doesn't exist"""
    username = 'admin'
    email = 'admin@summerfest.local'
    password = 'summerfest2025'
    
    if User.objects.filter(username=username).exists():
        print(f"Admin user '{username}' already exists.")
        return
    
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        first_name='System',
        last_name='Administrator'
    )
    
    print(f"Admin user created successfully!")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("\nYou can now log in to the admin interface at http://localhost:8000/admin/")
    print("Please change the password after first login!")

if __name__ == '__main__':
    create_admin_user()
