# Summerfest Registration System

A comprehensive web application for managing child registration and attendance for Lighthouse Church's Summerfest summer program.

## Features

- **Parent Registration**: Complete registration with all required fields and conditional validation
- **Child Management**: Add, edit, and manage children's details including medical and dietary requirements
- **QR Code System**: Automatic QR code generation for each child for easy check-in
- **Attendance Tracking**: Scan QR codes to register attendance and track check-in/check-out times
- **Teacher Dashboard**: Class management interface with emergency contact and medical information
- **Admin Interface**: Django admin for backend data management

## Quick Start (Windows)

### Prerequisites
- Python 3.8+ installed on your system
- Basic command line knowledge

### Setup Instructions

1. **Open PowerShell** and navigate to the project directory:
   ```powershell
   cd C:\Users\User\summerfest_registration
   ```

2. **Install dependencies** (already done if you followed the setup):
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Set up the database**:
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create an admin user**:
   ```powershell
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin account.

5. **Run the development server**:
   ```powershell
   python manage.py runserver
   ```

6. **Access the application**:
   - Main site: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## User Roles

### Parents/Guardians
- Register account with complete contact and emergency information
- Add and manage children's profiles
- View and download QR codes for each child
- Edit child details as needed

### Registration Team/Staff
- Scan QR codes to check children in
- Access attendance scanning interface
- View all registered children

### Teachers
- View class lists with attendance status
- Access emergency contact and medical information
- Check children in and out of classes
- Add notes about children's attendance

### Administrators
- Full access to Django admin interface
- Manage all user accounts and data
- Create teacher profiles
- Export data and generate reports

## Key Features Explained

### Conditional Fields
The registration forms include smart conditional logic:
- Additional information field appears when "Friend Recommended" is selected
- Church name field appears when "Yes" is selected for church attendance
- Dietary and medical detail fields appear when "Yes" is selected for those needs

### QR Code System
- Each child automatically gets a unique QR code upon registration
- QR codes can be downloaded or screenshotted for easy access
- Registration team can scan codes for instant check-in
- System prevents duplicate check-ins on the same day

### Security
- User authentication required for all sensitive areas
- Role-based access control (parents see only their children, teachers see their classes)
- Staff/admin privileges for attendance scanning and class management

## Deployment Options

### Local Testing (Current Setup)
- Perfect for testing and development
- Access via http://localhost:8000
- SQLite database (no additional setup required)

### Cloud Deployment (Future)
This application can be easily deployed to cloud platforms like:
- **Railway**: Simple deployment with automatic HTTPS
- **Render**: Free tier available, easy setup
- **Heroku**: Popular platform with good documentation
- **PythonAnywhere**: Python-focused hosting

### Church Website Integration
The application can be integrated into your church website by:
- Deploying to a subdomain (e.g., summerfest.yourchurch.org)
- Embedding registration forms in existing pages
- Customizing styling to match your church's branding

## Database Schema

### ParentProfile
- All required registration fields from CSV (26 fields total)
- Conditional validation and required fields
- Links to Django User model for authentication

### Child
- Complete child information with health and class details
- Automatic QR code generation
- Validation for age requirements (born after 2010)

### Attendance
- Daily check-in/check-out tracking
- Links to staff members who performed check-in/out
- Optional notes for each attendance record

### TeacherProfile
- Assigns teachers to specific classes
- Controls access to class management features

## Support

For issues or questions about this registration system, please contact your church's technical team or the developer who set up this system.

## Security Notes

- Change the SECRET_KEY in settings.py before production deployment
- Set DEBUG = False for production
- Configure proper ALLOWED_HOSTS for your domain
- Use environment variables for sensitive settings in production
