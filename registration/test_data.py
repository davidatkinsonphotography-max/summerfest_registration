"""
Test data utilities for creating sample users and data for site map testing
"""

from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import ParentProfile, Child, TeacherProfile, TeacherClassAssignment
from datetime import date
import uuid


def create_test_parent():
    """Create a test parent user with profile and return credentials"""
    username = "test_parent"
    password = "summerfest2024"
    email = "parent@test.com"
    
    # Delete existing test user if exists
    User.objects.filter(username=username).delete()
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Test",
        last_name="Parent"
    )
    
    # Create parent profile
    parent_profile = ParentProfile.objects.create(
        user=user,
        first_name="Test",
        last_name="Parent",
        street_address="123 Test Street",
        city="Test City",
        postcode="1234",
        email=email,
        phone_number="0123456789",
        how_heard_about="friend",
        additional_information="Created by test data generator",
        attends_church_regularly=True,
        which_church="Lighthouse Church",
        emergency_contact_name="Test Emergency Contact",
        emergency_contact_phone="0987654321",
        emergency_contact_relationship="other_parent",
        first_aid_consent=True,
        injury_waiver=True,
    )
    
    return {
        'username': username,
        'password': password,
        'user': user,
        'profile': parent_profile
    }


def create_test_children(parent_profile, count=18):
    """Create test children for a parent profile with varied realistic details"""
    import random
    
    children = []
    
    # Realistic child names
    first_names_boys = [
        'Liam', 'Noah', 'Oliver', 'Elijah', 'Lucas', 'Mason', 'Logan', 'Alexander',
        'Ethan', 'Jacob', 'Michael', 'Daniel', 'Henry', 'Jackson', 'Sebastian', 'Aiden',
        'Matthew', 'Samuel', 'David', 'Joseph', 'Carter', 'Owen', 'Wyatt', 'John'
    ]
    
    first_names_girls = [
        'Emma', 'Olivia', 'Ava', 'Sophia', 'Isabella', 'Charlotte', 'Amelia', 'Mia',
        'Harper', 'Evelyn', 'Abigail', 'Emily', 'Ella', 'Elizabeth', 'Camila', 'Luna',
        'Sofia', 'Avery', 'Mila', 'Aria', 'Scarlett', 'Penelope', 'Layla', 'Chloe'
    ]
    
    last_names = [
        'Anderson', 'Brown', 'Clark', 'Davis', 'Evans', 'Garcia', 'Harris', 'Jackson',
        'Johnson', 'Jones', 'Lee', 'Martin', 'Miller', 'Moore', 'Rodriguez', 'Smith',
        'Taylor', 'Thomas', 'Thompson', 'White', 'Williams', 'Wilson', 'Young', 'Lewis'
    ]
    
    # Class distribution - ensure good spread across all classes
    class_choices = [
        ('creche', 3),     # 3 children
        ('tackers', 4),    # 4 children  
        ('minis', 4),      # 4 children
        ('nitro', 4),      # 4 children
        ('56ers', 3),      # 3 children
    ]
    
    # Birth year ranges for each class (working backwards from 2026)
    class_birth_years = {
        'creche': (2024, 2025),    # 0-2 years old in 2026
        'tackers': (2021, 2023),   # 3-5 years old in 2026 (kindy in 2026)
        'minis': (2019, 2020),     # Years 1-2 in 2026
        'nitro': (2017, 2018),     # Years 3-4 in 2026  
        '56ers': (2015, 2016),     # Years 5-6 in 2026
    }
    
    # Dietary options
    dietary_needs = [
        '',
        'Gluten free',
        'Nut allergy', 
        'Vegetarian',
        'Dairy free',
        'No shellfish',
        'Halal',
    ]
    
    # Medical conditions  
    medical_conditions = [
        '',
        'Asthma inhaler required',
        'Severe nut allergy - EpiPen required',
        'Type 1 diabetes - blood sugar monitoring',
        'Epilepsy - medication as needed',
        'ADHD - medication at lunch',
        'Mild autism - needs quiet space when overwhelmed',
    ]
    
    child_index = 0
    
    # Create children distributed across classes
    for class_code, class_count in class_choices:
        birth_year_min, birth_year_max = class_birth_years[class_code]
        
        for i in range(class_count):
            if child_index >= count:
                break
                
            # Randomly choose gender and appropriate name
            gender = random.choice(['male', 'female'])
            if gender == 'male':
                first_name = random.choice(first_names_boys)
            else:
                first_name = random.choice(first_names_girls)
            
            last_name = random.choice(last_names)
            
            # Generate realistic birth date for class
            birth_year = random.randint(birth_year_min, birth_year_max)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Safe day for all months
            birth_date = date(birth_year, birth_month, birth_day)
            
            # Random dietary and medical needs (most children have none)
            has_dietary = random.random() < 0.25  # 25% chance
            dietary_detail = random.choice(dietary_needs[1:]) if has_dietary else ''
            
            has_medical = random.random() < 0.15  # 15% chance
            medical_detail = random.choice(medical_conditions[1:]) if has_medical else ''
            
            # Photo consent (90% yes)
            photo_consent = random.random() < 0.9
            
            child = Child.objects.create(
                parent=parent_profile,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=birth_date,
                gender=gender,
                child_class=class_code,
                has_dietary_needs=has_dietary,
                dietary_needs_detail=dietary_detail,
                has_medical_needs=has_medical,
                medical_allergy_details=medical_detail,
                photo_consent=photo_consent
            )
            children.append(child)
            child_index += 1
    
    return children


def create_test_teacher():
    """Create test teachers for different classes and return main teacher credentials"""
    # Clean up existing test teachers
    User.objects.filter(username__startswith="test_teacher").delete()
    
    teachers_created = []
    
    # Teacher assignments with realistic names
    teacher_data = [
        {
            'username': 'test_teacher',
            'first_name': 'Sarah',
            'last_name': 'Mitchell',
            'email': 'sarah.mitchell@test.com',
            'classes': [('minis', True)]  # (class_code, is_primary)
        },
        {
            'username': 'test_teacher_nitro',
            'first_name': 'David',
            'last_name': 'Chen',
            'email': 'david.chen@test.com',
            'classes': [('nitro', True)]
        },
        {
            'username': 'test_teacher_56ers',
            'first_name': 'Emma',
            'last_name': 'Rodriguez',
            'email': 'emma.rodriguez@test.com',
            'classes': [('56ers', True)]
        },
        {
            'username': 'test_teacher_tackers',
            'first_name': 'Michael',
            'last_name': 'Thompson',
            'email': 'michael.thompson@test.com',
            'classes': [('tackers', True), ('creche', False)]  # Primary for tackers, helper for creche
        }
    ]
    
    password = "summerfest2024"
    main_teacher = None
    
    for teacher_info in teacher_data:
        # Create user
        user = User.objects.create_user(
            username=teacher_info['username'],
            email=teacher_info['email'],
            password=password,
            first_name=teacher_info['first_name'],
            last_name=teacher_info['last_name']
        )
        
        # Create teacher profile
        teacher_profile = TeacherProfile.objects.create(
            user=user
        )
        
        # Assign classes
        for class_code, is_primary in teacher_info['classes']:
            TeacherClassAssignment.objects.create(
                teacher=teacher_profile,
                class_code=class_code,
                is_primary=is_primary
            )
        
        teacher_created = {
            'username': teacher_info['username'],
            'password': password,
            'user': user,
            'profile': teacher_profile
        }
        
        teachers_created.append(teacher_created)
        
        # Return the main teacher (first one) for backwards compatibility
        if teacher_info['username'] == 'test_teacher':
            main_teacher = teacher_created
    
    return main_teacher


def create_test_admin():
    """Create a test admin/staff user and return credentials"""
    username = "test_admin"
    password = "summerfest2024"
    email = "admin@test.com"
    
    # Delete existing test user if exists
    User.objects.filter(username=username).delete()
    
    # Create admin user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Test",
        last_name="Admin",
        is_staff=True,
        is_superuser=True
    )
    
    return {
        'username': username,
        'password': password,
        'user': user
    }


def get_test_credentials():
    """Get all available test user credentials"""
    credentials = []
    
    # Check if test users exist
    if User.objects.filter(username="test_parent").exists():
        credentials.append({
            'role': 'Parent',
            'username': 'test_parent',
            'password': 'summerfest2024',
            'description': 'Parent with children registered'
        })
    
    # Check for all teacher accounts
    teacher_accounts = [
        ('test_teacher', 'Sarah Mitchell - Minis class'),
        ('test_teacher_nitro', 'David Chen - Nitro class'),
        ('test_teacher_56ers', 'Emma Rodriguez - 56ers class'),
        ('test_teacher_tackers', 'Michael Thompson - Tackers/Creche classes')
    ]
    
    for username, description in teacher_accounts:
        if User.objects.filter(username=username).exists():
            credentials.append({
                'role': 'Teacher',
                'username': username,
                'password': 'summerfest2024',
                'description': description
            })
    
    if User.objects.filter(username="test_admin").exists():
        credentials.append({
            'role': 'Admin',
            'username': 'test_admin',
            'password': 'summerfest2024', 
            'description': 'Site administrator with full access'
        })
    
    return credentials


def cleanup_test_data():
    """Remove all test data"""
    # Remove parent and admin accounts
    User.objects.filter(username__in=["test_parent", "test_admin"]).delete()
    
    # Remove all teacher accounts (including the new ones)
    User.objects.filter(username__startswith="test_teacher").delete()
    
    return True
