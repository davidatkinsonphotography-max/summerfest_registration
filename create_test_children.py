#!/usr/bin/env python
"""
Simple script to create test children for testing class filters
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summerfest.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from registration.test_data import create_test_parent, create_test_children
from registration.models import Child
from datetime import date

def main():
    # Create parent if doesn't exist
    try:
        parent = create_test_parent()
        print(f"Created parent: {parent['username']}")
    except Exception as e:
        print(f"Parent creation error (may already exist): {e}")
        from django.contrib.auth.models import User
        from registration.models import ParentProfile
        user = User.objects.get(username='test_parent')
        parent = {'profile': user.parentprofile}
    
    # Remove existing test children to start fresh
    Child.objects.filter(parent=parent['profile']).delete()
    
    # Create children with different classes
    children_data = [
        {
            'first_name': 'Emma',
            'last_name': 'Test',
            'date_of_birth': date(2022, 5, 15),  # For creche
            'gender': 'female',
            'child_class': 'creche'
        },
        {
            'first_name': 'Jake', 
            'last_name': 'Test',
            'date_of_birth': date(2021, 8, 22),  # For tackers
            'gender': 'male',
            'child_class': 'tackers'
        },
        {
            'first_name': 'Sophie',
            'last_name': 'Test', 
            'date_of_birth': date(2018, 3, 10),  # For minis
            'gender': 'female',
            'child_class': 'minis'
        },
        {
            'first_name': 'Alex',
            'last_name': 'Test', 
            'date_of_birth': date(2015, 11, 5),  # For nitro
            'gender': 'male',
            'child_class': 'nitro'
        },
        {
            'first_name': 'Zoe',
            'last_name': 'Test', 
            'date_of_birth': date(2013, 7, 18),  # For 56ers
            'gender': 'female',
            'child_class': '56ers'
        }
    ]
    
    children = []
    for i, child_data in enumerate(children_data):
        child = Child.objects.create(
            parent=parent['profile'],
            **child_data,
            has_dietary_needs=i == 1,  # Second child has dietary needs
            dietary_needs_detail="Gluten free" if i == 1 else "",
            has_medical_needs=i == 3,  # Fourth child has medical needs
            medical_allergy_details="Peanut allergy" if i == 3 else "",
            photo_consent=True
        )
        children.append(child)
        print(f"Created: {child.first_name} {child.last_name} - {child.get_child_class_display()}")
    
    print(f"\nTotal children created: {len(children)}")
    print("Classes represented:")
    for code, name in Child.CLASS_CHOICES:
        count = len([c for c in children if c.child_class == code])
        if count > 0:
            print(f"  {name}: {count} child(ren)")

if __name__ == '__main__':
    main()
