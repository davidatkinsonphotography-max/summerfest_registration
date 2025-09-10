#!/usr/bin/env python
"""
Update teacher to be assigned to all classes
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summerfest.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from registration.models import TeacherClassAssignment, TeacherProfile
from django.contrib.auth.models import User

def main():
    try:
        teacher = User.objects.get(username='test_teacher')
        profile = teacher.teacherprofile
        
        # Clear existing assignments
        profile.class_assignments.all().delete()
        
        # Add all class assignments
        all_classes = [
            ('creche', 'Creche'),
            ('tackers', 'Little Tackers'), 
            ('minis', 'Minis'),
            ('nitro', 'Nitro'),
            ('56ers', '56ers')
        ]
        
        for code, name in all_classes:
            assignment = TeacherClassAssignment.objects.create(
                teacher=profile,
                class_code=code,
                is_primary=(code == 'minis')  # Make minis the primary
            )
            print(f"Added assignment: {name}")
        
        print(f"\nTeacher {teacher.get_full_name()} now assigned to:")
        for class_name in profile.get_assigned_class_names():
            print(f"  - {class_name}")
            
    except User.DoesNotExist:
        print("Test teacher not found. Please create teacher first.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
