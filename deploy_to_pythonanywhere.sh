#!/bin/bash

# PythonAnywhere Deployment Script for Summerfest Registration System
# Run this script in your PythonAnywhere Bash console

echo "=== Summerfest Registration System Deployment ==="
echo "This script will help you deploy to PythonAnywhere"
echo ""

# Variables - UPDATE THESE!
USERNAME="yourusername"  # Your PythonAnywhere username
PROJECT_NAME="summerfest"
GITHUB_REPO="https://github.com/yourusername/summerfest-registration.git"  # Your GitHub repo

echo "Step 1: Creating directory structure..."
mkdir -p ~/summerfest
mkdir -p ~/summerfest/logs
mkdir -p ~/summerfest/cache

echo "Step 2: Cloning repository..."
cd ~/summerfest
git clone $GITHUB_REPO .

echo "Step 3: Creating virtual environment..."
python3.9 -m venv venv
source venv/bin/activate

echo "Step 4: Installing dependencies..."
pip install -r requirements.txt

echo "Step 5: Setting up production settings..."
cp summerfest/production_settings.py summerfest/settings_production.py

echo "Step 6: Database setup..."
python manage.py migrate --settings=summerfest.settings_production

echo "Step 7: Collecting static files..."
python manage.py collectstatic --noinput --settings=summerfest.settings_production

echo "Step 8: Creating superuser (you'll need to do this manually)..."
echo "Run: python manage.py createsuperuser --settings=summerfest.settings_production"

echo ""
echo "=== MANUAL STEPS REQUIRED ==="
echo ""
echo "1. Update your WSGI file at /var/www/${USERNAME}_pythonanywhere_com_wsgi.py:"
echo ""
echo "import os"
echo "import sys"
echo ""
echo "# Add your project directory to the sys.path"
echo "path = '/home/${USERNAME}/summerfest'"
echo "if path not in sys.path:"
echo "    sys.path.insert(0, path)"
echo ""
echo "os.environ['DJANGO_SETTINGS_MODULE'] = 'summerfest.settings_production'"
echo ""
echo "from django.core.wsgi import get_wsgi_application"
echo "application = get_wsgi_application()"
echo ""
echo "2. Set up environment variables in PythonAnywhere:"
echo "   - Go to Web > Environment variables"
echo "   - Add: DJANGO_SECRET_KEY (generate at https://djecrety.ir/)"
echo "   - Add: STRIPE_PUBLISHABLE_KEY (your live key)"
echo "   - Add: STRIPE_SECRET_KEY (your live key)"
echo "   - Add: STRIPE_WEBHOOK_SECRET (from Stripe dashboard)"
echo "   - Add: EMAIL_HOST_USER (your email)"
echo "   - Add: EMAIL_HOST_PASSWORD (your app password)"
echo ""
echo "3. Update Static files mapping in PythonAnywhere Web tab:"
echo "   URL: /static/"
echo "   Directory: /home/${USERNAME}/summerfest/static"
echo ""
echo "4. Update Media files mapping:"
echo "   URL: /media/"
echo "   Directory: /home/${USERNAME}/summerfest/media"
echo ""
echo "5. Update settings_production.py with your actual domain and settings"
echo ""
echo "6. Set up Stripe webhook:"
echo "   - URL: https://${USERNAME}.pythonanywhere.com/payment/webhook/"
echo "   - Events: payment_intent.succeeded"
echo ""
echo "7. Create superuser:"
echo "   python manage.py createsuperuser --settings=summerfest.settings_production"
echo ""
echo "8. Test the application!"
echo ""
echo "Deployment script completed. Check the manual steps above."
