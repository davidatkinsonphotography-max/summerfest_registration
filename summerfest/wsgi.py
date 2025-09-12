"""
WSGI config for summerfest project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Add your project directory to the Python path
path = '/home/atkinsondp/summerfest_registration'
if path not in sys.path:
    sys.path.append(path)

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summerfest.settings')

# Activate your virtualenv
activate_this = '/home/atkinsondp/summerfest_registration/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
