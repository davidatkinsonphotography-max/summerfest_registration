# Fixing GitHub Secret Detection Issue

GitHub has blocked your push because it detected Stripe API keys in your commit history. Here's how to fix it:

## Option 1: Remove Secrets from Git History (Recommended)

Since the secrets are now in environment variables, we need to clean them from git history:

### Step 1: Install git-filter-repo (if not already installed)
```bash
pip install git-filter-repo
```

### Step 2: Remove the secrets from ALL commits
```bash
# Remove the specific Stripe keys from all commits
git filter-repo --replace-text <(echo 'REMOVED_STRIPE_PUBLISHABLE_KEY==>REMOVED_STRIPE_KEY')
git filter-repo --replace-text <(echo 'REMOVED_STRIPE_SECRET_KEY==>REMOVED_STRIPE_KEY')
```

### Step 3: Force push the cleaned history
```bash
git remote add origin https://github.com/yourusername/summerfest_registration.git
git push --force-with-lease origin main
```

## Option 2: Start Fresh (Alternative)

If the above is too complex, you can start with a fresh repo:

### Step 1: Rename current origin
```bash
git remote rename origin old-origin
```

### Step 2: Create new GitHub repo and push
```bash
# Create a new repository on GitHub
git remote add origin https://github.com/yourusername/summerfest_registration_clean.git
git push -u origin main
```

## After Either Option

1. **Test your app** to ensure it works with environment variables:
   ```bash
   python manage.py runserver
   ```

2. **Set up production environment variables** on PythonAnywhere:
   - Go to your PythonAnywhere Dashboard
   - Go to Tasks → Files → Open Bash Console
   - Navigate to your project directory
   - Create production .env file with LIVE Stripe keys

3. **Update your production_settings.py** domain names and paths

## Important Notes

- The `.env` file is now gitignored and will never be committed
- Your test Stripe keys are safely in the `.env` file
- For production, use LIVE Stripe keys in environment variables
- Never put secrets directly in code files again

## Environment Variables Needed for Production

```bash
DJANGO_SECRET_KEY=your_new_secret_key_here
DJANGO_DEBUG=False
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key_here
STRIPE_SECRET_KEY=sk_live_your_live_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
EMAIL_HOST_USER=your-email@yourchurch.org
EMAIL_HOST_PASSWORD=your-app-password
```
