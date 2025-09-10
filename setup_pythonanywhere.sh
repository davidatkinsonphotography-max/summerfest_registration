#!/bin/bash
# Automated setup script for PythonAnywhere deployment
# Run this in your PythonAnywhere bash console

echo "🚀 Setting up Summerfest Registration on PythonAnywhere..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: manage.py not found. Please run this script from your project directory.${NC}"
    echo "Expected: cd ~/summerfest_registration"
    exit 1
fi

echo -e "${BLUE}📁 Current directory: $(pwd)${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Creating virtual environment...${NC}"
    python3.10 -m venv venv
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️  Warning: .env file not found!${NC}"
    echo -e "${YELLOW}📝 You need to create a .env file with your production settings.${NC}"
    echo "Sample .env content:"
    echo ""
    echo "DJANGO_SECRET_KEY=your-new-production-secret-key"
    echo "DJANGO_DEBUG=False"
    echo "STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY"
    echo "STRIPE_SECRET_KEY=sk_live_YOUR_KEY"
    echo "STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET"
    echo "EMAIL_HOST_USER=your-email@church.org"
    echo "EMAIL_HOST_PASSWORD=your-app-password"
    echo ""
    echo "Create it with: nano .env"
    echo ""
    read -p "Press Enter to continue once you've created the .env file..."
fi

# Run Django setup commands
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
python manage.py migrate

echo -e "${YELLOW}📊 Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Check if superuser exists
echo -e "${YELLOW}👤 Checking for admin user...${NC}"
if python manage.py shell -c "from django.contrib.auth.models import User; print('Admin exists' if User.objects.filter(is_superuser=True).exists() else 'No admin')"; then
    echo -e "${GREEN}✅ Admin user check completed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Create superuser: python manage.py createsuperuser"
echo "2. Configure your PythonAnywhere web app settings"
echo "3. Set up static file mappings"
echo "4. Configure WSGI file"
echo "5. Set up Stripe webhooks"
echo ""
echo -e "${GREEN}📖 See PYTHONANYWHERE_DEPLOYMENT.md for detailed instructions${NC}"
echo ""
echo -e "${YELLOW}🌐 Your site will be available at: https://yourusername.pythonanywhere.com${NC}"
echo -e "${YELLOW}Replace 'yourusername' with your actual PythonAnywhere username${NC}"
