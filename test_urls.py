#!/usr/bin/env python
"""
Test URL resolution for export views
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summerfest.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from django.contrib.auth.models import User
from registration.export_views_fixed import export_dashboard

def test_urls():
    print("=== URL Resolution Test ===")
    
    try:
        url = reverse('export_dashboard')
        print(f"✅ export_dashboard URL resolves to: {url}")
    except Exception as e:
        print(f"❌ export_dashboard URL failed: {e}")
    
    try:
        url = reverse('export_all_data')
        print(f"✅ export_all_data URL resolves to: {url}")
    except Exception as e:
        print(f"❌ export_all_data URL failed: {e}")
    
    # Test direct path resolution
    print("\n=== Direct Path Resolution ===")
    try:
        match = resolve('/export/')
        print(f"✅ /export/ resolves to: {match.func.__name__}")
    except Exception as e:
        print(f"❌ /export/ resolution failed: {e}")
    
    try:
        match = resolve('/export/all/')
        print(f"✅ /export/all/ resolves to: {match.func.__name__}")
    except Exception as e:
        print(f"❌ /export/all/ resolution failed: {e}")
    
    # Test view function directly
    print("\n=== Direct View Test ===")
    try:
        factory = RequestFactory()
        request = factory.get('/admin/export/')
        
        # Create a test user
        user = User.objects.filter(is_staff=True, is_superuser=True).first()
        if user:
            request.user = user
            response = export_dashboard(request)
            print(f"✅ export_dashboard view works: Status {response.status_code}")
        else:
            print("❌ No admin user found for testing")
    except Exception as e:
        print(f"❌ Direct view test failed: {e}")

if __name__ == '__main__':
    test_urls()
