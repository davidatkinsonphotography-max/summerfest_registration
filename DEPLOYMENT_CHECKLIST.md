# Summerfest Registration - Production Deployment Checklist

## 1. Security Settings (CRITICAL - Must Change!)

### `summerfest/settings.py` Changes:

```python
# 1. Generate a new SECRET_KEY for production
SECRET_KEY = 'your-new-secret-key-here'  # Generate at: https://djecrety.ir/

# 2. Set DEBUG to False
DEBUG = False

# 3. Add your domain to ALLOWED_HOSTS
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
```

## 2. Stripe Configuration (CRITICAL!)

Replace test keys with LIVE keys:

```python
# Get these from your Stripe Dashboard > Developers > API Keys
STRIPE_PUBLISHABLE_KEY = 'pk_live_...'  # Your live publishable key
STRIPE_SECRET_KEY = 'sk_live_...'       # Your live secret key
STRIPE_WEBHOOK_SECRET = 'whsec_...'     # Your webhook secret
```

⚠️ **WARNING**: Live Stripe keys will charge real money! Test thoroughly first!

## 3. Email Configuration

```python
# Update with your actual email settings
EMAIL_HOST_USER = 'summerfest@yourdomain.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Summerfest Registration <summerfest@yourdomain.com>'
```

## 4. Database Setup on PythonAnywhere

1. In PythonAnywhere console:
   ```bash
   python manage.py collectstatic
   python manage.py migrate
   python manage.py createsuperuser
   ```

## 5. Static Files Configuration

Already configured in settings.py - should work automatically on PythonAnywhere.

## 6. Create Initial Admin Users

Run these commands in PythonAnywhere console:

```bash
# Create superuser admin
python manage.py createsuperuser

# Create test data (optional - for testing)
python manage.py shell
>>> from registration.test_data import *
>>> create_test_admin()
>>> create_test_teacher()
```

## 7. Webhook Setup (For Stripe Payments)

1. In Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://yourusername.pythonanywhere.com/payment/webhook/`
3. Select events: `payment_intent.succeeded`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

## 8. SSL/HTTPS Settings

Add to `settings.py` for production:

```python
# HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

## 9. Environment Variables (Recommended)

For better security, use environment variables:

```python
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

## 10. Testing Checklist

Before going live, test:

- [ ] User registration works
- [ ] Login/logout works
- [ ] Password reset works (check email delivery)
- [ ] Child registration works
- [ ] QR code generation works
- [ ] Payment processing works (with test data first!)
- [ ] Teacher dashboard works
- [ ] Admin dashboard works
- [ ] Data export works
- [ ] All class filters work
- [ ] Mobile responsiveness

## 11. Backup Strategy

- [ ] Set up regular database backups
- [ ] Backup media files (QR codes)
- [ ] Document recovery procedures

## 12. Monitoring

- [ ] Set up error logging
- [ ] Monitor payment transactions
- [ ] Monitor user registrations

## 13. Go-Live Steps

1. Deploy to PythonAnywhere
2. Test thoroughly with test Stripe keys
3. Update Stripe to live keys
4. Test one small transaction
5. Announce to users

## Security Notes

- **Never commit sensitive keys to GitHub**
- Use PythonAnywhere's environment variables for secrets
- Regularly update Django and dependencies
- Monitor for security updates

## Support Contacts

- Stripe Support: https://support.stripe.com/
- PythonAnywhere Help: https://help.pythonanywhere.com/
- Django Documentation: https://docs.djangoproject.com/

---

**Remember**: Test everything thoroughly before switching to live Stripe keys!
