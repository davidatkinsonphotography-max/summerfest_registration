from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinLengthValidator
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image


class ParentProfile(models.Model):
    """Extended profile for parents/guardians"""
    
    HEAR_ABOUT_CHOICES = [
        ('friend', 'My Friend Recommended (please tell us who in additional information)'),
        ('church', 'At Lighthouse Church'),
        ('kids_club', "Lighthouse Kids' Club"),
        ('facebookpage', "Facebook page … [please fill in the page name in ‘additional information’]"),
        ('facebookad', "Facebook advertisement"),
        ('schoolflyerhome', "School Flyer sent home ... [please fill in which school in ‘additional information’]"),
        ('schoolnews', "School Newsletter … [please fill in which school in ‘additional information’]"),
        ('schoolflyerschool', "School Flyer collected from school ... [please fill in which school in ‘additional information’]"),
        ('preschool', "Flyer at Preschool/day care ... [please fill in where in 'additional information'"),
        ('flyer', "A Summerfest flyer given to me at… [please fill in where in ‘additional information’]"),
        ('banner', "A banner/poster located at ... … [please fill in where in ‘additional information’]"),
        ('email', "I received an email"),
        ('websearch', "Web Search"),
        ('homevisit', "Someone visited me"),
        ('newspaper', "Newspaper/Magazine … [please fill in where in ‘additional information’]"),
        ('radio', "Rhema FM"),
        ('scripture', "My child's scripture class"),
    ]
    
    EMERGENCY_RELATIONSHIP_CHOICES = [
        ('other_parent', 'Other Parent'),
        ('grandparent', 'Grandparent'),
        ('uncle_aunty', 'Uncle/Aunty'),
        ('Sibling', 'Sibling'),
        ('family_friend', 'Family Friend'),
        ('neighbour', 'Neighbour'),
        ('other', 'Other'),    
    ]
    
    CHURCH_ATTENDANCE_CHOICES = [
        ('lighthouse', 'Yes - Lighthouse Church'),
        ('other', 'Yes - Other church'),
        ('no', 'No'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Basic Information (Fields 1-7)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    postcode = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{4}$', 'Postcode must be 4 digits')]
    )
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{1,10}$', 'Phone number must be up to 10 digits')]
    )
    
    # Program Information (Fields 8-11)
    how_heard_about = models.CharField(max_length=20, choices=HEAR_ABOUT_CHOICES)
    additional_information = models.TextField(blank=True)
    attends_church_regularly = models.BooleanField()
    which_church = models.CharField(max_length=200, blank=True)
    
    # Emergency Contact (Fields 12-14)
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{1,10}$', 'Phone number must be up to 10 digits')]
    )
    emergency_contact_relationship = models.CharField(
        max_length=20, 
        choices=EMERGENCY_RELATIONSHIP_CHOICES
    )
    
    # Consent (Fields 15-16)
    first_aid_consent = models.BooleanField(default=False)
    injury_waiver = models.BooleanField(default=False)
    
    # Parent QR Code for attendance
    parent_qr_code_id = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    parent_qr_code_image = models.ImageField(upload_to='parent_qr_codes/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.parent_qr_code_image:
            self.generate_parent_qr_code()
    
    def generate_parent_qr_code(self):
        """Generate QR code for parent (covers all their children)"""
        qr_data = f"summerfest_parent_{self.parent_qr_code_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f'qr_parent_{self.id}_{self.parent_qr_code_id}.png'
        self.parent_qr_code_image.save(filename, File(buffer), save=False)
        super().save(update_fields=['parent_qr_code_image'])
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Child(models.Model):
    """Child registration details"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    CLASS_CHOICES = [
        ('creche', "Creche - 0-2yrs old"),
        ('tackers', "Little Tackers - 3yrs-Kindy (2026)"),
        ('minis', "Minis - School Years 1-2 (2026)"),
        ('nitro', "Nitro - School Years 3-4 (2026)"),
        ('56ers', "56ers - School Years 5-6 (2026)"),
    ]
    
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='children')
    
    # Basic Child Information (Fields 17-21)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(
        help_text="Child must be born after January 1, 2010"
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    child_class = models.CharField(max_length=20, choices=CLASS_CHOICES)
    
    # Dietary Requirements (Fields 22-23)
    has_dietary_needs = models.BooleanField(default=False)
    dietary_needs_detail = models.TextField(blank=True)
    
    # Medical Requirements (Fields 24-25)
    has_medical_needs = models.BooleanField(default=False)
    medical_allergy_details = models.TextField(blank=True)
    
    # Photo Consent (Field 26)
    photo_consent = models.BooleanField(default=True)
    
    # QR Code for attendance
    qr_code_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.date_of_birth and self.date_of_birth < date(2010, 1, 1):
            raise ValidationError('Child must be born after January 1, 2010')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code_image:
            self.generate_qr_code()
    
    def generate_qr_code(self):
        """Generate QR code for child attendance"""
        qr_data = f"summerfest_child_{self.qr_code_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f'qr_child_{self.id}_{self.qr_code_id}.png'
        self.qr_code_image.save(filename, File(buffer), save=False)
        super().save(update_fields=['qr_code_image'])
    
    def get_class_short_name(self):
        """Get abbreviated class name for admin/teacher views"""
        class_mapping = {
            'creche': 'Creche',
            'tackers': 'Little Tackers', 
            'minis': 'Minis',
            'nitro': 'Nitro',
            '56ers': '56ers',
        }
        return class_mapping.get(self.child_class, self.get_child_class_display())
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_child_class_display()})"


class Attendance(models.Model):
    """Track child attendance"""
    
    STATUS_CHOICES = [
        ('not_arrived', 'Not yet arrived'),
        ('checked_in', 'Checked in'),
        ('in_class', 'In class'),
        ('picked_up', 'Picked up'),
    ]
    
    STATUS_COLORS = {
        'not_arrived': '#6c757d',  # Grey
        'checked_in': '#28a745',  # Green  
        'in_class': '#007bff',    # Blue
        'picked_up': '#6f42c1',  # Purple
    }
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='checked_in')
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='checked_in_children')
    checked_out_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_out_children')
    notes = models.TextField(blank=True)
    
    # Payment tracking fields
    charge_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    charge_reason = models.TextField(blank=True, help_text='Explanation of charge calculation')
    
    class Meta:
        ordering = ['-date', '-time_in']
    
    def __str__(self):
        return f"{self.child.first_name} {self.child.last_name} - {self.date} ({self.get_status_display()})"
    
    def get_status_color(self):
        """Get the hex color for the current status"""
        return self.STATUS_COLORS.get(self.status, '#6c757d')
    
    def can_change_to_status(self, new_status):
        """Check if status change is valid"""
        status_order = ['not_arrived', 'checked_in', 'in_class', 'picked_up']
        current_index = status_order.index(self.status)
        new_index = status_order.index(new_status)
        # Can only move forward in status or stay the same
        return new_index >= current_index


class TeacherClassAssignment(models.Model):
    """Intermediate model for teacher class assignments"""
    
    CLASS_CHOICES = [
        ('creche', "Creche - 0-2yrs old"),
        ('tackers', "Little Tackers - 3yrs-Kindy (2026)"),
        ('minis', "Minis - School Years 1-2 (2026)"),
        ('nitro', "Nitro - School Years 3-4 (2026)"),
        ('56ers', "56ers - School Years 5-6 (2026)"),
    ]
    
    teacher = models.ForeignKey('TeacherProfile', on_delete=models.CASCADE, related_name='class_assignments')
    class_code = models.CharField(max_length=20, choices=CLASS_CHOICES)
    is_primary = models.BooleanField(default=False, help_text="Is this teacher the primary teacher for this class?")
    
    class Meta:
        unique_together = ['teacher', 'class_code']
    
    def get_class_short_name(self):
        """Get abbreviated class name for admin/teacher views"""
        class_mapping = {
            'creche': 'Creche',
            'tackers': 'Little Tackers', 
            'minis': 'Minis',
            'nitro': 'Nitro',
            '56ers': '56ers',
        }
        return class_mapping.get(self.class_code, self.get_class_code_display())
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.get_class_code_display()}"


class TeacherProfile(models.Model):
    """Teacher/Staff profile for class management"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __str__(self):
        classes = self.get_assigned_class_names()
        if classes:
            return f"{self.user.get_full_name()} - {', '.join(classes)}"
        return f"{self.user.get_full_name()} - No classes assigned"
    
    def get_assigned_class_names(self, abbreviated=False):
        """Get list of assigned class display names"""
        assignments = self.class_assignments.all()
        if abbreviated:
            return [assignment.get_class_short_name() for assignment in assignments]
        return [assignment.get_class_code_display() for assignment in assignments]
    
    def get_assigned_class_codes(self):
        """Get list of assigned class codes"""
        return list(self.class_assignments.values_list('class_code', flat=True))
    
    def is_assigned_to_class(self, class_code):
        """Check if teacher is assigned to a specific class"""
        return self.class_assignments.filter(class_code=class_code).exists()
    
    def get_primary_classes(self):
        """Get classes where this teacher is the primary teacher"""
        return self.class_assignments.filter(is_primary=True)


# Payment System Models and Constants

# Pricing Constants
CHILD_DAILY_RATE = Decimal('6.00')  # $6 per child per day
FAMILY_DAILY_RATE = Decimal('12.00')  # $12 per family per day
CHILD_WEEKLY_CAP = Decimal('20.00')   # $20 per child per week
FAMILY_WEEKLY_CAP = Decimal('40.00')  # $40 per family per week


class PaymentAccount(models.Model):
    """Payment account for each family"""
    
    parent_profile = models.OneToOneField(ParentProfile, on_delete=models.CASCADE, related_name='payment_account')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    weekly_charge_child = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    weekly_charge_family = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    current_week_start = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment Account - {self.parent_profile}"
    
    def get_current_week_start(self):
        """Get the start of the current Summerfest week (Monday)"""
        today = date.today()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        return week_start
    
    def reset_weekly_charges_if_needed(self):
        """Reset weekly charges if we're in a new week"""
        current_week = self.get_current_week_start()
        if self.current_week_start != current_week:
            self.weekly_charge_child = Decimal('0.00')
            self.weekly_charge_family = Decimal('0.00')
            self.current_week_start = current_week
            self.save()
    
    def get_weekly_sign_ins_count(self):
        """Count total sign-ins this week for all children in family"""
        self.reset_weekly_charges_if_needed()
        week_start = self.get_current_week_start()
        week_end = week_start + timedelta(days=6)
        
        # Count all sign-ins this week for this family's children
        return Attendance.objects.filter(
            child__parent=self.parent_profile,
            date__range=[week_start, week_end]
        ).count()
    
    def get_total_children_count(self):
        """Get total number of children registered for this family"""
        return self.parent_profile.children.count()
    
    def calculate_charge_for_signin(self, child):
        """Calculate charge for a single child sign-in based on new rules"""
        # Check if child already signed in today (no double charging)
        today = date.today()
        existing_attendance = Attendance.objects.filter(
            child=child,
            date=today
        ).exists()
        
        if existing_attendance:
            return Decimal('0.00')  # No charge for same child same day
        
        weekly_sign_ins = self.get_weekly_sign_ins_count()
        total_children = self.get_total_children_count()
        
        if total_children == 1:
            # Single child pricing
            if weekly_sign_ins < 3:
                return Decimal('6.00')  # First 3 sign-ins: $6
            elif weekly_sign_ins == 3:
                return Decimal('2.00')  # 4th sign-in: $2  
            else:
                return Decimal('0.00')  # 5th+ sign-ins: $0
        else:
            # Multiple children pricing (2+)
            if weekly_sign_ins < 6:
                return Decimal('6.00')  # First 6 sign-ins: $6
            elif weekly_sign_ins == 6:
                return Decimal('4.00')  # 7th sign-in: $4
            else:
                return Decimal('0.00')  # 8th+ sign-ins: $0
    
    def get_daily_charge(self, children_attending_today):
        """Get the actual charge for today given the children attending"""
        total_charge = Decimal('0.00')
        for child in children_attending_today:
            total_charge += self.calculate_charge_for_signin(child)
        return total_charge
    
    def has_sufficient_balance(self, required_amount):
        """Check if account has sufficient balance"""
        return self.balance >= required_amount
    
    def add_funds(self, amount, description="Funds added"):
        """Add funds to the account"""
        self.balance += amount
        self.save()
        
        # Create transaction record
        PaymentTransaction.objects.create(
            payment_account=self,
            amount=amount,
            transaction_type='credit',
            description=description
        )
    
    def deduct_funds(self, amount, description="Daily attendance charge"):
        """Deduct funds from the account"""
        self.balance -= amount
        self.save()
        
        # Create transaction record
        PaymentTransaction.objects.create(
            payment_account=self,
            amount=-amount,
            transaction_type='debit',
            description=description
        )


class PaymentTransaction(models.Model):
    """Individual payment transactions"""
    
    TRANSACTION_TYPES = [
        ('credit', 'Credit - Money Added'),
        ('debit', 'Debit - Money Deducted'),
    ]
    
    PAYMENT_METHODS = [
        ('stripe', 'Online Card Payment'),
        ('cash', 'Cash Payment'),
        ('eftpos', 'EFTPOS Payment'),
        ('system', 'System Transaction'),
    ]
    
    payment_account = models.ForeignKey(PaymentAccount, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='system')
    description = models.CharField(max_length=200)
    
    # Stripe integration fields
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True, null=True)
    
    # Staff recording manual payments
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        sign = '+' if self.transaction_type == 'credit' else '-'
        return f"{sign}${abs(self.amount)} - {self.description}"


class Pass(models.Model):
    """Pass system for Summerfest attendance"""
    
    PASS_TYPES = [
        ('daily_child', 'Daily Child Pass ($6)'),
        ('daily_family', 'Daily Family Pass ($12)'),
        ('weekly_child', 'Weekly Child Pass ($20)'),
        ('weekly_family', 'Weekly Family Pass ($40)'),
    ]
    
    PASS_PRICES = {
        'daily_child': Decimal('6.00'),
        'daily_family': Decimal('12.00'),
        'weekly_child': Decimal('20.00'),
        'weekly_family': Decimal('40.00'),
    }
    
    type = models.CharField(max_length=20, choices=PASS_TYPES)
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='passes')
    valid_from = models.DateField()
    valid_to = models.DateField()
    
    # Stripe integration
    stripe_payment_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)
    
    # Purchase tracking
    purchased_at = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.parent.first_name} {self.parent.last_name} ({self.valid_from} to {self.valid_to})"
    
    def is_valid_for_date(self, check_date=None):
        """Check if pass is valid for the given date (default: today)"""
        if check_date is None:
            check_date = date.today()
        return self.valid_from <= check_date <= self.valid_to
    
    def is_family_pass(self):
        """Check if this is a family pass (covers multiple children)"""
        return self.type in ['daily_family', 'weekly_family']
    
    def get_price(self):
        """Get the price for this pass type"""
        return self.PASS_PRICES.get(self.type, Decimal('0.00'))
    
    @classmethod
    def get_valid_passes_for_parent(cls, parent, check_date=None):
        """Get all valid passes for a parent on a given date"""
        if check_date is None:
            check_date = date.today()
        
        return cls.objects.filter(
            parent=parent,
            valid_from__lte=check_date,
            valid_to__gte=check_date
        ).order_by('-created_at')
    
    @classmethod
    def has_valid_pass_for_attendance(cls, parent, check_date=None):
        """Check if parent has any valid pass for attendance on given date"""
        valid_passes = cls.get_valid_passes_for_parent(parent, check_date)
        return valid_passes.exists()


class DailyAttendanceCharge(models.Model):
    """Track daily charges for attendance - DEPRECATED: Use Pass system instead"""
    
    payment_account = models.ForeignKey(PaymentAccount, on_delete=models.CASCADE, related_name='daily_charges')
    date = models.DateField()
    children_count = models.IntegerField()
    calculated_charge = models.DecimalField(max_digits=10, decimal_places=2)
    actual_charge = models.DecimalField(max_digits=10, decimal_places=2)  # After weekly caps
    
    # Track which children were charged for
    children = models.ManyToManyField(Child, related_name='daily_charges')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['payment_account', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - {self.children_count} children - ${self.actual_charge}"
