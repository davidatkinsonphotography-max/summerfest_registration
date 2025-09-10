# Summerfest Registration - PythonAnywhere Deployment Guide

This guide will walk you through deploying your Summerfest Registration system to PythonAnywhere.

## Prerequisites
- PythonAnywhere account (Hacker plan or higher for custom domains)
- Your GitHub repository: https://github.com/davidatkinsonphotography-max/summerfest_registration

## Step 1: Clone Repository on PythonAnywhere

1. **Open a Bash Console** on PythonAnywhere Dashboard
2. **Clone your repository**:
```bash
cd ~
git clone https://github.com/davidatkinsonphotography-max/summerfest_registration.git
cd summerfest_registration
```

## Step 2: Set Up Virtual Environment

```bash
# Create virtual environment (Python 3.10 recommended)
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Create Production Environment Variables

Create a `.env` file in your project directory:

```bash
nano .env
```

Add these environment variables (replace with your actual values):

```bash
# Django Settings
DJANGO_SECRET_KEY=your-new-production-secret-key-here
DJANGO_DEBUG=False

# Stripe Configuration (LIVE KEYS for production!)
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_PUBLISHABLE_KEY
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY  
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET

# Email Configuration
EMAIL_HOST_USER=summerfest@yourchurch.org
EMAIL_HOST_PASSWORD=your-email-app-password

# Database (if using MySQL - optional)
# DATABASE_URL=mysql://yourusername:password@yourusername.mysql.pythonanywhere-services.com/yourusername$summerfest
```

**Important**: 
- Generate a new SECRET_KEY at: https://djecrety.ir/
- Use LIVE Stripe keys (pk_live_... and sk_live_...) for production
- Never use test keys in production

## Step 4: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Step 5: Configure Web App

1. **Go to PythonAnywhere Dashboard → Web**
2. **Create a new web app**:
   - Choose "Manual configuration"
   - Select Python 3.10
3. **Configure paths**:
   - Source code: `/home/yourusername/summerfest_registration`
   - Working directory: `/home/yourusername/summerfest_registration`

## Step 6: WSGI Configuration

Edit your WSGI file (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):

```python
import os
import sys

# Add your project directory to sys.path
path = '/home/yourusername/summerfest_registration'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'summerfest.settings'

# Import Django WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 7: Static Files Configuration

In your PythonAnywhere Web tab, add these static file mappings:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/summerfest_registration/static` |
| `/media/` | `/home/yourusername/summerfest_registration/media` |

## Step 8: Set Up Stripe Webhooks

1. **Go to Stripe Dashboard → Developers → Webhooks**
2. **Add endpoint**: `https://yourusername.pythonanywhere.com/payment/webhook/`
3. **Select events**:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
4. **Copy webhook signing secret** to your `.env` file

## Step 9: Test Your Deployment

1. **Reload your web app** in PythonAnywhere Web tab
2. **Visit your site**: `https://yourusername.pythonanywhere.com`
3. **Test key features**:
   - User registration
   - Login/logout
   - QR code generation
   - Payment system (with test cards first!)
   - Admin panel access

## Step 10: Security Checklist

- [ ] `DEBUG = False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] Live Stripe keys configured
- [ ] Email settings configured
- [ ] Webhook endpoint secured
- [ ] HTTPS enabled (automatic on PythonAnywhere)
- [ ] Admin user created with strong password

## Troubleshooting

### Common Issues:

1. **Static files not loading**:
   - Check static file mappings
   - Run `python manage.py collectstatic --noinput`

2. **Database errors**:
   - Ensure migrations are run: `python manage.py migrate`
   - Check database permissions

3. **Email not working**:
   - Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
   - Enable "Less secure app access" or use app-specific password

4. **Stripe webhook failures**:
   - Check webhook URL is correct
   - Verify webhook secret matches

### Useful Commands:

```bash
# Check logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Restart web app (after code changes)
# Go to Web tab and click "Reload"

# Update code from GitHub
cd ~/summerfest_registration
git pull origin main
# Then reload web app
```

## Going Live Checklist

Before announcing to parents:

- [ ] Test with real (small) Stripe payment
- [ ] Verify QR codes work on mobile devices  
- [ ] Test registration flow end-to-end
- [ ] Verify email notifications work
- [ ] Test teacher and admin dashboards
- [ ] Backup database
- [ ] Monitor error logs for first few users

## Support

If you encounter issues:
1. Check PythonAnywhere error logs
2. Review Django debug information
3. Test individual components (payments, QR codes, etc.)
4. Contact PythonAnywhere support if server-related

Your Summerfest Registration System should now be live at:
**https://yourusername.pythonanywhere.com**

Remember to replace "yourusername" with your actual PythonAnywhere username throughout this guide!
