# WSGI configuration file for PythonAnywhere
# Copy this content to your WSGI file: /var/www/yourusername_pythonanywhere_com_wsgi.py

import os
import sys

# Add your project directory to the Python path
# Replace 'yourusername' with your actual PythonAnywhere username
project_home = '/home/yourusername/summerfest_registration'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'summerfest.settings'

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Optional: For production, you might want to use production settings instead
# os.environ['DJANGO_SETTINGS_MODULE'] = 'summerfest.production_settings'
