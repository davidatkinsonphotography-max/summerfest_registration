from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import ParentProfile, Child, Attendance, TeacherProfile
from .forms import ParentRegistrationForm, ChildRegistrationForm, AttendanceForm, CheckoutForm, ManualSignInForm, PasswordResetRequestForm
from .test_data import create_test_parent, create_test_children, create_test_teacher, create_test_admin, get_test_credentials, cleanup_test_data

def send_qr_code_email(child, parent_profile):
    """Send QR code via email to parent"""
    # Ensure QR code is generated
    if not child.qr_code_image:
        child.generate_qr_code()
    
    subject = f'Summerfest 2026 QR Code for {child.first_name}'
    
    # Email context
    context = {
        'child': child,
        'parent_profile': parent_profile,
        'qr_code_data': f'summerfest_child_{child.qr_code_id}',
    }
    
    # Render HTML template
    html_content = render_to_string('registration/emails/qr_code_email.html', context)
    text_content = strip_tags(html_content)
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[parent_profile.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    # Attach QR code image
    if child.qr_code_image:
        email.attach_file(child.qr_code_image.path)
    
    email.send()

from django.shortcuts import render
from django.http import Http404

# list of templates you want to preview (filenames without .html)
ALLOWED_PREVIEWS = [
    "add_child",
    "attendance_scan",
    "checkout_child",
    "child_qr_code",
    "dashboard",
    "edit_child",
    "home",
    "login",
    "parent_register",
    "profile_edit",
    "teacher_dashboard",
]

def preview_template(request, page_name):
    """
    Renders registration/<page_name>.html if it's in ALLOWED_PREVIEWS,
    otherwise 404s. Safe and simple.
    """
    if page_name not in ALLOWED_PREVIEWS:
        raise Http404("Page not found")
    return render(request, f"registration/{page_name}.html")

def preview_index(request):
    """
    A small index page that lists all previewable templates.
    """
    pages = sorted(ALLOWED_PREVIEWS)
    return render(request, "registration/preview_index.html", {"pages": pages})

def home(request):
    """Landing page for Summerfest registration"""
    return render(request, 'registration/home.html')


def parent_register(request):
    """Parent registration view"""
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create parent profile with all the additional fields
            parent_profile = ParentProfile.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                street_address=form.cleaned_data['street_address'],
                city=form.cleaned_data['city'],
                postcode=form.cleaned_data['postcode'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                how_heard_about=form.cleaned_data['how_heard_about'],
                additional_information=form.cleaned_data['additional_information'],
                attends_church_regularly=form.cleaned_data['attends_church_regularly'],
                which_church=form.cleaned_data['which_church'],
                emergency_contact_name=form.cleaned_data['emergency_contact_name'],
                emergency_contact_phone=form.cleaned_data['emergency_contact_phone'],
                emergency_contact_relationship=form.cleaned_data['emergency_contact_relationship'],
                first_aid_consent=form.cleaned_data['first_aid_consent'],
                injury_waiver=form.cleaned_data['injury_waiver'],
            )
            
            login(request, user)
            messages.success(request, 'Registration successful! Now you can add your children.')
            return redirect('dashboard')
    else:
        form = ParentRegistrationForm()
    
    return render(request, 'registration/parent_register.html', {'form': form})


@login_required
def dashboard(request):
    """Smart dashboard that routes users to appropriate interface based on their role"""
    user = request.user
    
    # Check if user has parent profile first - show parent dashboard
    try:
        parent_profile = request.user.parentprofile
        children = parent_profile.children.all()
        return render(request, 'registration/dashboard.html', {
            'parent_profile': parent_profile,
            'children': children
        })
    except ParentProfile.DoesNotExist:
        pass
    
    # If no parent profile, check if user is admin or staff - redirect to admin dashboard
    if user.is_staff:
        return redirect('teacher_dashboard')
    
    # Check if user has teacher profile - redirect to teacher dashboard
    if hasattr(user, 'teacherprofile'):
        return redirect('teacher_dashboard')
    
    # User has no profiles - redirect to registration
    messages.error(request, 'Please complete your registration first.')
    return redirect('parent_register')


@login_required
def add_child(request):
    """Add a new child"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = parent_profile
            child.save()
            
            # Send QR code email to parent
            try:
                send_qr_code_email(child, parent_profile)
                messages.success(request, f'{child.first_name} has been registered successfully! QR code emailed to {parent_profile.email}')
            except Exception as e:
                messages.warning(request, f'{child.first_name} has been registered successfully! However, the QR code email could not be sent. You can view the QR code from your dashboard.')
            
            return redirect('dashboard')
    else:
        form = ChildRegistrationForm()
    
    return render(request, 'registration/add_child.html', {'form': form})


@login_required
def edit_child(request, child_id):
    """Edit an existing child's details"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    child = get_object_or_404(Child, id=child_id, parent=parent_profile)
    
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, f'{child.first_name}\'s details have been updated!')
            return redirect('dashboard')
    else:
        form = ChildRegistrationForm(instance=child)
    
    return render(request, 'registration/edit_child.html', {'form': form, 'child': child})


@login_required
def remove_child(request, child_id):
    """Remove a child from parent's account"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    child = get_object_or_404(Child, id=child_id, parent=parent_profile)
    
    if request.method == 'POST':
        child_name = f"{child.first_name} {child.last_name}"
        child.delete()
        messages.success(request, f'{child_name} has been removed from your account.')
        return redirect('dashboard')
    
    return render(request, 'registration/remove_child.html', {'child': child})


@login_required
def child_qr_code(request, child_id):
    """Display QR code for a child"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    child = get_object_or_404(Child, id=child_id, parent=parent_profile)
    
    if not child.qr_code_image:
        child.generate_qr_code()
    
    return render(request, 'registration/child_qr_code.html', {'child': child})


def is_staff_or_teacher(user):
    """Check if user is staff or has teacher profile"""
    return user.is_staff or hasattr(user, 'teacherprofile')


@login_required
@user_passes_test(is_staff_or_teacher)
def attendance_scan(request):
    """QR code scanning interface for registration team"""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            child = form.cleaned_data['qr_code_data']
            
            # Check if child is already checked in today
            today_attendance = Attendance.objects.filter(
                child=child,
                date=timezone.now().date(),
                time_out__isnull=True
            ).first()
            
            if today_attendance:
                return JsonResponse({
                    'status': 'already_checked_in',
                    'message': f'{child.first_name} {child.last_name} is already checked in.',
                    'child_name': f'{child.first_name} {child.last_name}',
                    'class': child.get_child_class_display()
                })
            
            # Process check-in with new payment calculator
            from .payment_calculator import PaymentCalculator
            
            try:
                attendance, charge_amount, charge_reason = PaymentCalculator.process_checkin_with_payment(
                    child=child,
                    check_date=PaymentCalculator.get_current_aest_date(),
                    check_in_time=PaymentCalculator.get_current_aest_datetime()
                )
                
                # Update attendance record with staff who checked them in
                attendance.checked_in_by = request.user
                attendance.save(update_fields=['checked_in_by'])
                
            except Exception as e:
                # Handle calculation errors (e.g., already checked in)
                if "Already checked in today" in str(e) or charge_reason == "Already checked in today":
                    return JsonResponse({
                        'status': 'already_checked_in',
                        'message': f'{child.first_name} {child.last_name} is already checked in.',
                        'child_name': f'{child.first_name} {child.last_name}',
                        'class': child.get_child_class_display()
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Check-in failed: {str(e)}'
                    })
            
            return JsonResponse({
                'status': 'success',
                'message': f'{child.first_name} {child.last_name} has been checked in!',
                'child_name': f'{child.first_name} {child.last_name}',
                'class': child.get_child_class_display(),
                'time': attendance.time_in.strftime('%H:%M'),
                'charge': f'${charge_amount}' if charge_amount > 0 else 'Free',
                'charge_reason': charge_reason,
                'remaining_balance': f'${child.parent.payment_account.balance if hasattr(child.parent, "payment_account") else "0.00"}',
                # Additional child information for persistent check-in list
                'dietary_needs': child.has_dietary_needs,
                'medical_needs': child.has_medical_needs,
                'photo_consent': child.photo_consent,
                'dietary_details': child.dietary_needs_detail or '',
                'medical_details': child.medical_allergy_details or ''
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid QR code'
            })
    else:
        form = AttendanceForm()
    
    return render(request, 'registration/attendance_scan.html', {'form': form})


@login_required
@user_passes_test(is_staff_or_teacher)
def teacher_dashboard(request):
    """Teacher dashboard for class management"""
    # Get class filter from query parameter
    selected_class = request.GET.get('class', '')
    
    # Get teacher's assigned classes or show all if staff
    if request.user.is_staff:
        children = Child.objects.all()
        teacher_classes = ['creche', 'tackers', 'minis', 'nitro', '56ers']  # All classes for admins
    else:
        try:
            teacher_profile = request.user.teacherprofile
            # Get all class codes this teacher is assigned to
            assigned_class_codes = teacher_profile.get_assigned_class_codes()
            teacher_classes = assigned_class_codes
            if assigned_class_codes:
                children = Child.objects.filter(child_class__in=assigned_class_codes)
            else:
                children = Child.objects.none()
        except TeacherProfile.DoesNotExist:
            children = Child.objects.none()
            teacher_classes = []
    
    # Apply class filter if specified
    if selected_class and selected_class in ['creche', 'tackers', 'minis', 'nitro', '56ers']:
        children = children.filter(child_class=selected_class)
    
    # Get today's attendance
    today = timezone.now().date()
    attendance_today = Attendance.objects.filter(date=today)
    
    # Organize children by class and attendance status
    children_data = []
    for child in children:
        attendance = attendance_today.filter(child=child).first()
        
        # Get payment account balance
        balance = Decimal('0.00')
        try:
            if hasattr(child.parent, 'payment_account'):
                balance = child.parent.payment_account.balance
        except Exception:
            balance = Decimal('0.00')
        
        children_data.append({
            'child': child,
            'attendance': attendance,
            'is_present': attendance is not None and attendance.time_out is None,
            'balance': balance
        })
    
    return render(request, 'registration/teacher_dashboard.html', {
        'children_data': children_data,
        'today': today,
        'selected_class': selected_class,
        'teacher_classes': teacher_classes
    })


@login_required
@user_passes_test(is_staff_or_teacher)
def checkout_child(request, child_id):
    """Check out a child"""
    child = get_object_or_404(Child, id=child_id)
    
    # Find today's attendance record
    today = timezone.now().date()
    attendance = get_object_or_404(Attendance, child=child, date=today, time_out__isnull=True)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            attendance.time_out = timezone.now()
            attendance.checked_out_by = request.user
            attendance.notes = form.cleaned_data['notes']
            attendance.save()
            
            messages.success(request, f'{child.first_name} {child.last_name} has been checked out.')
            
            # Preserve class filter if it was set
            class_filter = request.GET.get('class')
            if class_filter:
                return redirect(f'/teacher_dashboard/?class={class_filter}')
            else:
                return redirect('teacher_dashboard')
    else:
        form = CheckoutForm(initial={'child_id': child.id})
    
    return render(request, 'registration/checkout_child.html', {
        'form': form,
        'child': child,
        'attendance': attendance
    })


@login_required
def profile_edit(request):
    """Edit parent profile"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    if request.method == 'POST':
        # Create a form instance with the current profile data
        form_data = request.POST.copy()
        form_data['username'] = request.user.username
        
        # For profile editing, we don't want to change password
        form = ParentRegistrationForm(form_data, instance=request.user)
        form.fields.pop('password1', None)
        form.fields.pop('password2', None)
        
        if form.is_valid():
            # Update parent profile fields
            for field in ['first_name', 'last_name', 'street_address', 'city', 'postcode',
                         'email', 'phone_number', 'how_heard_about', 'additional_information',
                         'attends_church_regularly', 'which_church', 'emergency_contact_name',
                         'emergency_contact_phone', 'emergency_contact_relationship']:
                if field in form.cleaned_data:
                    setattr(parent_profile, field, form.cleaned_data[field])
            
            parent_profile.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('dashboard')
    else:
        # Pre-populate form with existing data
        initial_data = {
            'username': request.user.username,
            'first_name': parent_profile.first_name,
            'last_name': parent_profile.last_name,
            'street_address': parent_profile.street_address,
            'city': parent_profile.city,
            'postcode': parent_profile.postcode,
            'email': parent_profile.email,
            'phone_number': parent_profile.phone_number,
            'how_heard_about': parent_profile.how_heard_about,
            'additional_information': parent_profile.additional_information,
            'church_attendance_choice': 'lighthouse' if parent_profile.which_church == 'Lighthouse Church' else ('other' if parent_profile.attends_church_regularly else 'no'),
            'which_church': parent_profile.which_church,
            'emergency_contact_name': parent_profile.emergency_contact_name,
            'emergency_contact_phone': parent_profile.emergency_contact_phone,
            'emergency_contact_relationship': parent_profile.emergency_contact_relationship,
        }
        form = ParentRegistrationForm(initial=initial_data)
        form.fields.pop('password1', None)
        form.fields.pop('password2', None)
    
    return render(request, 'registration/profile_edit.html', {'form': form})


def site_map(request):
    """Comprehensive site map for testing all functionality - password protected"""
    # Password protection for sitemap
    if not request.session.get('sitemap_authenticated'):
        if request.method == 'POST':
            password = request.POST.get('password')
            if password == 'Mk1sprite2bdi':
                request.session['sitemap_authenticated'] = True
            else:
                messages.error(request, 'Incorrect password')
                return render(request, 'registration/sitemap_password.html')
        else:
            return render(request, 'registration/sitemap_password.html')
    # Handle test data creation
    if request.GET.get('create'):
        create_type = request.GET.get('create')
        try:
            if create_type == 'parent':
                parent_data = create_test_parent()
                children = create_test_children(parent_data['profile'], count=18)  # Enhanced test data
                messages.success(request, f"Created test parent '{parent_data['username']}' with {len(children)} children distributed across all classes. Password: {parent_data['password']}")
            elif create_type == 'teacher':
                teacher_data = create_test_teacher()
                messages.success(request, f"Created test teacher '{teacher_data['username']}'. Password: {teacher_data['password']}")
            elif create_type == 'admin':
                admin_data = create_test_admin()
                messages.success(request, f"Created test admin '{admin_data['username']}'. Password: {admin_data['password']}")
            elif create_type == 'cleanup':
                cleanup_test_data()
                messages.success(request, "Cleaned up all test data")
        except Exception as e:
            messages.error(request, f"Error creating test data: {str(e)}")
        
        return redirect('site_map')
    
    # Define URL groups by role/permission
    url_groups = {
        'Anonymous (Public)': [
            ('Home Page', '/', 'Landing page - start here'),
            ('Parent Registration', '/parent_register/', 'Sign up new parents'),
            ('Login', '/login/', 'Login for existing users'),
            ('Template Previews', '/preview/', 'View all templates (development only)'),
        ],
        'Authenticated Parent': [
            ('Dashboard', '/dashboard/', 'Parent dashboard - view children'),
            ('Add Child', '/add_child/', 'Register a new child'),
            ('Edit Profile', '/profile_edit/', 'Update parent information'),
            ('Payment Dashboard', '/payment/dashboard/', 'View account balance and payment history'),
            ('Add Funds', '/payment/add_funds/', 'Add money to account via credit card'),
            # Dynamic URLs will be added if test data exists
        ],
        'Teacher/Staff Only': [
            ('Attendance Scan', '/attendance_scan/', 'QR code scanning for check-in'),
            ('Teacher Dashboard', '/teacher_dashboard/', 'Class management'),
            ('Manual Sign-In', '/manual_sign_in/', 'Sign in children without QR codes'),
            ('Manual Payment Entry', '/payment/manual/', 'Record cash/EFTPOS payments'),
            ('Payment Account Lookup', '/payment/lookup/', 'Search parent payment accounts'),
            # Dynamic checkout URLs will be added if children exist
        ],
        'Admin/Superuser': [
            ('Django Admin', '/admin/', 'Full administrative interface'),
            ('Data Export Dashboard', '/export/', 'Export all registration data to CSV'),
            ('Download Complete Report', '/export/all/', 'Download comprehensive CSV report'),
        ]
    }
    
    # Add dynamic URLs if test data exists
    test_parent_user = None
    test_children = []
    if Child.objects.filter(parent__user__username='test_parent').exists():
        test_children = Child.objects.filter(parent__user__username='test_parent')
        for child in test_children:
            url_groups['Authenticated Parent'].append(
                (f'Edit {child.first_name}', f'/child/{child.id}/edit/', f'Edit details for {child.first_name} {child.last_name}')
            )
            url_groups['Authenticated Parent'].append(
                (f'{child.first_name} QR Code', f'/child/{child.id}/qr/', f'View QR code for {child.first_name}')
            )
            url_groups['Authenticated Parent'].append(
                (f'Remove {child.first_name}', f'/child/{child.id}/remove/', f'Remove {child.first_name} {child.last_name} from account')
            )
            url_groups['Teacher/Staff Only'].append(
                (f'Checkout {child.first_name}', f'/checkout/{child.id}/', f'Check out {child.first_name} {child.last_name}')
            )
    
    # Get user authentication status
    user = request.user
    auth_status = {
        'is_authenticated': user.is_authenticated,
        'is_parent': user.is_authenticated and hasattr(user, 'parentprofile'),
        'is_teacher': user.is_authenticated and (hasattr(user, 'teacherprofile') or user.is_staff),
        'is_admin': user.is_authenticated and user.is_staff,
        'username': user.username if user.is_authenticated else None
    }
    
    # Get available test credentials
    test_credentials = get_test_credentials()
    
    # Sample data status
    sample_data = {
        'has_test_parent': Child.objects.filter(parent__user__username='test_parent').exists(),
        'has_test_teacher': TeacherProfile.objects.filter(user__username='test_teacher').exists(),
        'has_test_admin': User.objects.filter(username='test_admin', is_staff=True).exists(),
        'children_count': Child.objects.filter(parent__user__username='test_parent').count()
    }
    
    context = {
        'url_groups': url_groups,
        'auth_status': auth_status,
        'test_credentials': test_credentials,
        'sample_data': sample_data,
        'test_children': test_children,
    }
    
    return render(request, 'registration/site_map.html', context)


@login_required
@user_passes_test(is_staff_or_teacher)
def manual_sign_in(request):
    """Manual sign-in for children when parents forget QR codes"""
    parent_profile = None
    children = None
    search_info = None
    
    if request.method == 'POST':
        if 'lookup' in request.POST:
            # Parent lookup form
            form = ManualSignInForm(request.POST)
            if form.is_valid():
                from .payment_calculator import PaymentCalculator
                parent_profile, children = form.get_parent_and_children()
                search_info = form.get_search_info()
                
                # Add today's attendance data for each child
                if children:
                    today = PaymentCalculator.get_current_aest_date()
                    children_with_attendance = []
                    for child in children:
                        today_attendance = Attendance.objects.filter(
                            child=child,
                            date=today
                        ).first()
                        children_with_attendance.append({
                            'child': child,
                            'today_attendance': today_attendance,
                            'is_checked_in': today_attendance is not None
                        })
                    children = children_with_attendance
                # Keep form data for the template
                form = ManualSignInForm(initial={'parent_username': form.cleaned_data['parent_username']})
            else:
                # Form is invalid for lookup
                form = ManualSignInForm(request.POST)
                parent_profile = None
                children = None
                search_info = None
        
        elif 'sign_in' in request.POST:
            # Child sign-in processing
            child_ids = request.POST.getlist('child_ids')
            parent_username = request.POST.get('parent_username')
            
            if child_ids and parent_username:
                # Re-lookup parent using username
                temp_form = ManualSignInForm({'parent_username': parent_username})
                if temp_form.is_valid():
                    parent_profile, _ = temp_form.get_parent_and_children()
                    search_info = temp_form.get_search_info()
                    signed_in_children = []
                    payment_errors = []
                    
                    from .payment_calculator import PaymentCalculator
                    
                    for child_id in child_ids:
                        try:
                            child = Child.objects.get(id=child_id, parent=parent_profile)
                            
                            # Check if already signed in today (using PaymentCalculator)
                            if PaymentCalculator.has_child_checked_in_today(child, PaymentCalculator.get_current_aest_date()):
                                messages.warning(request, f'{child.first_name} {child.last_name} is already signed in today.')
                                continue
                            
                            # Process check-in with payment calculator
                            try:
                                attendance, charge_amount, charge_reason = PaymentCalculator.process_checkin_with_payment(
                                    child=child,
                                    check_date=PaymentCalculator.get_current_aest_date(),
                                    check_in_time=PaymentCalculator.get_current_aest_datetime()
                                )
                                
                                # Update attendance record with staff who checked them in
                                attendance.checked_in_by = request.user
                                attendance.save(update_fields=['checked_in_by'])
                                
                                signed_in_children.append(child)
                                
                            except Exception as payment_error:
                                # Handle insufficient balance
                                charge_amount, charge_reason = PaymentCalculator.calculate_charge_for_checkin(child)
                                from .payment_views import get_or_create_payment_account
                                payment_account = get_or_create_payment_account(parent_profile)
                                if charge_amount > payment_account.balance:
                                    payment_errors.append({
                                        'child': child,
                                        'required': charge_amount,
                                        'shortfall': charge_amount - payment_account.balance,
                                        'reason': charge_reason
                                    })
                            
                        except Child.DoesNotExist:
                            messages.error(request, f"Child not found or doesn't belong to this parent.")
                    
                    # Show success messages
                    if signed_in_children:
                        child_names = [f"{child.first_name} {child.last_name}" for child in signed_in_children]
                        messages.success(request, f"Successfully signed in: {', '.join(child_names)}")
                    
                    # Show payment errors
                    if payment_errors:
                        for error in payment_errors:
                            child = error['child']
                            shortfall = error['shortfall']
                            reason = error.get('reason', 'Insufficient balance')
                            messages.error(request, f"{child.first_name} {child.last_name}: {reason}. Need ${shortfall:.2f} more.")
                    
                    # Clear form after processing
                    if signed_in_children and not payment_errors:
                        form = ManualSignInForm()
                        parent_profile = None
                        children = None
                    else:
                        # Keep the lookup results if there were payment errors
                        from .payment_calculator import PaymentCalculator
                        today = PaymentCalculator.get_current_aest_date()
                        children_with_attendance = []
                        for child in parent_profile.children.all():
                            today_attendance = Attendance.objects.filter(
                                child=child,
                                date=today
                            ).first()
                            children_with_attendance.append({
                                'child': child,
                                'today_attendance': today_attendance,
                                'is_checked_in': today_attendance is not None
                            })
                        children = children_with_attendance
                        form = ManualSignInForm(initial={'parent_username': parent_username})
                else:
                    messages.error(request, "Invalid search query.")
                    form = ManualSignInForm()
                    parent_profile = None
                    children = None
                    search_info = None
            else:
                messages.error(request, "Please select at least one child to sign in.")
                form = ManualSignInForm()
                parent_profile = None
                children = None
                search_info = None
        else:
            # Unknown POST action
            form = ManualSignInForm()
            parent_profile = None
            children = None
            search_info = None
    else:
        form = ManualSignInForm()
    
    context = {
        'form': form,
        'parent_profile': parent_profile,
        'children': children,
        'search_info': search_info,
    }
    
    return render(request, 'registration/manual_sign_in.html', context)


@login_required
@user_passes_test(is_staff_or_teacher)
def manual_checkin_child(request, child_id):
    """API endpoint for manual check-in of individual children from teacher dashboard"""
    import json
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})
    
    try:
        child = get_object_or_404(Child, id=child_id)
        
        # Check if child is already checked in today
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(
            child=child,
            date=today,
            time_out__isnull=True
        ).first()
        
        if today_attendance:
            return JsonResponse({
                'status': 'already_checked_in',
                'message': f'{child.first_name} {child.last_name} is already checked in today.'
            })
        
        # Process check-in with new payment calculator
        from .payment_calculator import PaymentCalculator
        
        try:
            attendance, charge_amount, charge_reason = PaymentCalculator.process_checkin_with_payment(
                child=child,
                check_date=PaymentCalculator.get_current_aest_date(),
                check_in_time=PaymentCalculator.get_current_aest_datetime()
            )
            
            # Update attendance record with staff who checked them in
            attendance.checked_in_by = request.user
            attendance.save(update_fields=['checked_in_by'])
            
            return JsonResponse({
                'status': 'success',
                'message': f'{child.first_name} {child.last_name} has been checked in successfully!',
                'child_name': f'{child.first_name} {child.last_name}',
                'time': attendance.time_in.strftime('%H:%M'),
                'charge': f'{charge_amount:.2f}' if charge_amount > 0 else '0.00',
                'charge_reason': charge_reason,
                'remaining_balance': f'{child.parent.payment_account.balance if hasattr(child.parent, "payment_account") else Decimal("0.00"):.2f}'
            })
            
        except Exception as e:
            # Check if it's because child is already checked in
            if "Already checked in today" in str(e):
                return JsonResponse({
                    'status': 'already_checked_in',
                    'message': f'{child.first_name} {child.last_name} is already checked in today.'
                })
            else:
                # Handle insufficient balance or other errors
                charge_amount, charge_reason = PaymentCalculator.calculate_charge_for_checkin(child)
                if "Daily family cap reached" in charge_reason:
                    return JsonResponse({
                        'status': 'success_no_charge',
                        'message': f'{child.first_name} {child.last_name} checked in - daily family cap reached',
                        'charge_reason': charge_reason
                    })
                else:
                    # Get payment account balance
                    from .payment_views import get_or_create_payment_account
                    payment_account = get_or_create_payment_account(child.parent)
                    
                    # Assume insufficient balance if we get here
                    return JsonResponse({
                        'status': 'payment_required',
                        'message': f'Insufficient balance for {child.first_name} {child.last_name}',
                        'child_name': f'{child.first_name} {child.last_name}',
                        'current_balance': f'{payment_account.balance:.2f}',
                        'required_charge': f'{charge_amount:.2f}',
                        'shortfall': f'{(charge_amount - payment_account.balance):.2f}',
                        'charge_reason': charge_reason
                    })
        
    except Child.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Child not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})


@login_required
def custom_logout(request):
    """Custom logout view to ensure proper redirect"""
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    from django.contrib import messages
    
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')


@login_required
@user_passes_test(is_staff_or_teacher)
def change_child_status(request, child_id):
    """API endpoint for changing child attendance status"""
    import json
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})
    
    try:
        child = get_object_or_404(Child, id=child_id)
        
        # Parse the request body
        data = json.loads(request.body)
        new_status = data.get('status')
        
        # Find today's attendance record
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            child=child,
            date=today
        ).first()
        
        if not attendance:
            return JsonResponse({'status': 'error', 'message': 'Child is not checked in today'})
        
        # Validate status transition
        if not attendance.can_change_to_status(new_status):
            return JsonResponse({
                'status': 'error', 
                'message': f'Cannot change from {attendance.get_status_display()} to {dict(attendance.STATUS_CHOICES)[new_status]}'
            })
        
        # Update status
        old_status = attendance.get_status_display()
        attendance.status = new_status
        attendance.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'{child.first_name} {child.last_name} status changed from {old_status} to {attendance.get_status_display()}',
            'new_status': attendance.get_status_display()
        })
        
    except Child.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Child not found'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid request data'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})


@login_required
@user_passes_test(lambda user: user.is_staff or user.is_superuser)
def admin_dashboard(request):
    """Admin dashboard for check-in and payment processing"""
    # Get class filter from query parameter
    selected_class = request.GET.get('class', '')
    
    # Get all children with today's attendance data
    children = Child.objects.select_related('parent', 'parent__payment_account').all()
    
    # Apply class filter if specified
    if selected_class and selected_class in ['creche', 'tackers', 'minis', 'nitro', '56ers']:
        children = children.filter(child_class=selected_class)
    
    today = timezone.now().date()
    attendance_today = Attendance.objects.filter(date=today)
    
    # Organize children by attendance status
    children_data = []
    for child in children:
        attendance = attendance_today.filter(child=child).first()
        children_data.append({
            'child': child,
            'attendance': attendance,
        })
    
    return render(request, 'registration/admin_dashboard.html', {
        'children_data': children_data,
        'today': today,
        'selected_class': selected_class
    })


@login_required
@user_passes_test(lambda user: user.is_staff or user.is_superuser)
def admin_add_payment(request):
    """API endpoint for admin to add cash/EFTPOS payments"""
    import json
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'})
    
    try:
        data = json.loads(request.body)
        parent_id = data.get('parent_id')
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'cash')
        
        if not parent_id or not amount:
            return JsonResponse({'status': 'error', 'message': 'Parent ID and amount are required'})
        
        amount = float(amount)
        if amount <= 0 or amount > 100:
            return JsonResponse({'status': 'error', 'message': 'Amount must be between $1 and $100'})
        
        # Get parent profile
        parent_profile = get_object_or_404(ParentProfile, id=parent_id)
        
        # Get or create payment account
        from .payment_views import get_or_create_payment_account
        payment_account = get_or_create_payment_account(parent_profile)
        
        # Add funds
        payment_account.add_funds(
            amount, 
            f"Cash/EFTPOS payment recorded by {request.user.get_full_name() or request.user.username}"
        )
        
        # Update the transaction to record who added it
        latest_transaction = payment_account.transactions.first()
        if latest_transaction:
            latest_transaction.payment_method = payment_method
            latest_transaction.recorded_by = request.user
            latest_transaction.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Added ${amount:.2f} to {parent_profile.first_name} {parent_profile.last_name} account',
            'new_balance': f'{payment_account.balance:.2f}'
        })
        
    except ParentProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Parent not found'})
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid amount'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid request data'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})


def password_reset(request):
    """Password reset request form - allows parents to reset their password via email"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                # Get the parent profile and user
                parent_profile = ParentProfile.objects.get(email=email)
                user = parent_profile.user
                
                # Generate a new temporary password
                new_password = get_random_string(10)  # 10 character random password
                
                # Ensure the password meets our requirements by adding capital letter and number if needed
                import random
                import string
                if not any(c.isupper() for c in new_password):
                    new_password = new_password[:5] + random.choice(string.ascii_uppercase) + new_password[5:]
                if not any(c.isdigit() for c in new_password):
                    new_password = new_password[:7] + random.choice(string.digits) + new_password[7:]
                
                # Update user's password
                user.set_password(new_password)
                user.save()
                
                # Send email with new password
                subject = 'Summerfest Password Reset'
                message = f"""Hello {parent_profile.first_name},

Your password has been reset for your Summerfest registration account.

Your new temporary password is: {new_password}

For security reasons, please log in and change this password as soon as possible.

Your username is: {user.username}
Login at: {request.build_absolute_uri('/login/')}

If you did not request this password reset, please contact us immediately.

Best regards,
Summerfest Team"""
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, f'A new password has been sent to {email}. Please check your email and log in with the new password.')
                    return redirect('login')
                    
                except Exception as e:
                    # If email fails, still show success to user for security
                    messages.success(request, f'If an account with email {email} exists, a new password has been sent to that address.')
                    return redirect('login')
                    
            except ParentProfile.DoesNotExist:
                # Don't reveal that the email doesn't exist for security
                messages.success(request, f'If an account with email {email} exists, a new password has been sent to that address.')
                return redirect('login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'registration/password_reset.html', {'form': form})
