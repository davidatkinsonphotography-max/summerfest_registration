from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import ParentProfile, Child, ParentInteraction
from .widgets import ThreeFieldDateField
from datetime import date
from decimal import Decimal
import re


class ParentRegistrationForm(UserCreationForm):
    """Parent/Guardian registration form"""
    
    # Basic Information (Fields 1-7)
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    street_address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postcode = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'\d{4}', 'title': 'Enter 4 digits'})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'\d{1,10}', 'title': 'Enter up to 10 digits'})
    )
    
    # Program Information (Fields 8-11)
    how_heard_about = forms.ChoiceField(
        choices=ParentProfile.HEAR_ABOUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    additional_information = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    church_attendance_choice = forms.ChoiceField(
        choices=[
            ('lighthouse', 'Yes - Lighthouse Church'),
            ('other', 'Yes - Other church'),
            ('no', 'No')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Do you attend a church on a regular basis?"
    )
    which_church = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Which church do you attend?"
    )
    
    # Emergency Contact (Fields 12-14)
    emergency_contact_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    emergency_contact_phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'\d{1,10}', 'title': 'Enter up to 10 digits'})
    )
    emergency_contact_relationship = forms.ChoiceField(
        choices=ParentProfile.EMERGENCY_RELATIONSHIP_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Consent (Fields 15-16)
    first_aid_consent = forms.BooleanField(
        required=True,
        label="I give permission for necessary first aid to be administered by a first aid officer",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    injury_waiver = forms.BooleanField(
        required=True,
        label="I understand that while all care will be taken to ensure the safety of children and adults participating in this event, no liability can be accepted for an injury occurring during Summerfest.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Remove empty choice from dropdown fields
        if 'how_heard_about' in self.fields:
            self.fields['how_heard_about'].empty_label = None
        if 'emergency_contact_relationship' in self.fields:
            self.fields['emergency_contact_relationship'].empty_label = None
    
    def clean_attends_church_regularly(self):
        # Convert church_attendance_choice to boolean for backward compatibility
        choice = self.cleaned_data.get('church_attendance_choice', 'no')
        return choice in ['lighthouse', 'other']
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            # Check minimum length
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for at least one capital letter
            if not re.search(r'[A-Z]', password):
                raise ValidationError("Password must contain at least 1 capital letter (A-Z).")
            
            # Check for at least one number
            if not re.search(r'\d', password):
                raise ValidationError("Password must contain at least 1 number (0-9).")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        how_heard = cleaned_data.get('how_heard_about')
        additional_info = cleaned_data.get('additional_information')
        church_choice = cleaned_data.get('church_attendance_choice')
        which_church = cleaned_data.get('which_church')
        
        # Set the boolean field for backward compatibility
        cleaned_data['attends_church_regularly'] = church_choice in ['lighthouse', 'other']
        
        # Set which_church based on choice
        if church_choice == 'lighthouse':
            cleaned_data['which_church'] = 'Lighthouse Church'
        elif church_choice == 'other' and not which_church:
            raise ValidationError("Please specify which church you attend.")
        elif church_choice == 'no':
            cleaned_data['which_church'] = ''
        
        # Conditional validation for additional information
        # Made non-mandatory as per user request - no longer raises ValidationError
        # if how_heard == 'friend' and not additional_info:
        #     raise ValidationError("Please tell us who recommended Summerfest in the additional information field.")
        
        return cleaned_data


class ChildRegistrationForm(forms.ModelForm):
    """Child registration form"""
    
    date_of_birth = ThreeFieldDateField(
        help_text="Child must be born after January 1, 2010"
    )
    
    has_dietary_needs = forms.ChoiceField(
        choices=[('False', 'No'), ('True', 'Yes')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Does your child have any dietary needs?"
    )
    
    has_medical_needs = forms.ChoiceField(
        choices=[('False', 'No'), ('True', 'Yes')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Does your child have any medical needs or allergies?"
    )
    
    class Meta:
        model = Child
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'child_class',
            'has_dietary_needs', 'dietary_needs_detail',
            'has_medical_needs', 'medical_allergy_details',
            'photo_consent'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'child_class': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'dietary_needs_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_allergy_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'photo_consent': 'I give permission for photos of my child to be taken during Summerfest',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove empty choice from gender and child_class fields
        if 'gender' in self.fields:
            self.fields['gender'].empty_label = None
        if 'child_class' in self.fields:
            self.fields['child_class'].empty_label = None
        
        # Set photo consent to be checked by default for new forms
        if not self.instance.pk:  # Only for new children, not when editing
            self.fields['photo_consent'].initial = True
    
    def clean_has_dietary_needs(self):
        value = self.cleaned_data['has_dietary_needs']
        return value == 'True'
    
    def clean_has_medical_needs(self):
        value = self.cleaned_data['has_medical_needs']
        return value == 'True'
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        if dob < date(2010, 1, 1):
            raise ValidationError("Child must be born after January 1, 2010")
        return dob
    
    def clean(self):
        cleaned_data = super().clean()
        has_dietary = cleaned_data.get('has_dietary_needs')
        dietary_detail = cleaned_data.get('dietary_needs_detail')
        has_medical = cleaned_data.get('has_medical_needs')
        medical_detail = cleaned_data.get('medical_allergy_details')
        
        # Conditional validation for dietary needs
        if has_dietary and not dietary_detail:
            raise ValidationError("Please provide details about dietary needs.")
        
        # Conditional validation for medical needs
        if has_medical and not medical_detail:
            raise ValidationError("Please provide details about medical needs/allergies.")
        
        return cleaned_data


class AttendanceForm(forms.Form):
    """Form for QR code attendance scanning"""
    
    qr_code_data = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan QR code or enter code manually',
            'id': 'qr-input'
        })
    )
    
    def clean_qr_code_data(self):
        data = self.cleaned_data['qr_code_data']
        if not data.startswith('summerfest_child_'):
            raise ValidationError("Invalid QR code format")
        
        try:
            uuid_part = data.replace('summerfest_child_', '')
            child = Child.objects.get(qr_code_id=uuid_part)
            return child
        except Child.DoesNotExist:
            raise ValidationError("Child not found with this QR code")


class CheckoutForm(forms.Form):
    """Form for checking children out"""
    
    child_id = forms.IntegerField(widget=forms.HiddenInput())
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes'})
    )


class AddFundsForm(forms.Form):
    """Form for parents to add funds to their account"""
    
    def __init__(self, *args, **kwargs):
        from django.conf import settings
        super().__init__(*args, **kwargs)
        # Build dynamic choices with 1.2x credit shown
        try:
            multiplier = Decimal(settings.ONLINE_PAYMENT_BONUS_MULTIPLIER)
        except Exception:
            multiplier = Decimal('1.20')
        def credit(amount: Decimal) -> Decimal:
            return (amount * multiplier).quantize(Decimal('0.01'))
        def single_label(amount: Decimal, days: int) -> str:
            c = credit(amount)
            day_word = 'day' if days == 1 else 'days'
            return f"${amount:.0f} {days} {day_word} - Single child (pay ${amount:.0f} online, we will credit ${c} to your balance)"
        def family_label(amount: Decimal, days: int) -> str:
            c = credit(amount)
            day_word = 'day' if days == 1 else 'days'
            return f"${amount:.0f} {days} {day_word} - Family (pay ${amount:.0f} online, we will credit ${c} to your balance)"

        # Build 8 distinct options (including duplicates for amounts under different groups)
        choices = [
            ('5.00-single', single_label(Decimal('5.00'), 1)),
            ('10.00-single', single_label(Decimal('10.00'), 2)),
            ('15.00-single', single_label(Decimal('15.00'), 3)),
            ('20.00-single', single_label(Decimal('20.00'), 4)),
            ('10.00-family', family_label(Decimal('10.00'), 1)),
            ('20.00-family', family_label(Decimal('20.00'), 2)),
            ('30.00-family', family_label(Decimal('30.00'), 3)),
            ('40.00-family', family_label(Decimal('40.00'), 4)),
            ('custom', 'Other Amount')
        ]
        self.fields['amount_choice'] = forms.ChoiceField(
            choices=choices,
            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            label="Select amount to add"
        )
    
    custom_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=Decimal('1.00'),
        max_value=Decimal('40.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1.00', 'max': '40.00'}),
        label="Other amount"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        amount_choice = cleaned_data.get('amount_choice')
        custom_amount = cleaned_data.get('custom_amount')
        
        if amount_choice == 'custom':
            if not custom_amount:
                raise ValidationError("Please enter an amount.")
            if custom_amount < Decimal('1.00'):
                raise ValidationError("Minimum amount is $1.00.")
            if custom_amount > Decimal('40.00'):
                raise ValidationError("Maximum amount is $40.00.")
        
        return cleaned_data
    
    def get_amount(self):
        """Get the selected amount as a Decimal"""
        choice = self.cleaned_data['amount_choice']
        if choice == 'custom':
            return self.cleaned_data['custom_amount']
        # Values like '10.00-single' or '10.00-family' => extract numeric part
        numeric = choice.split('-', 1)[0]
        return Decimal(numeric)


class ManualPaymentForm(forms.Form):
    """Form for staff to record manual payments (cash/eftpos)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate parent choices
        parent_choices = [('', '--- Select a Parent ---')]
        parents = ParentProfile.objects.select_related('user').order_by('last_name', 'first_name')
        for parent in parents:
            display_name = f"{parent.last_name}, {parent.first_name} - {parent.user.username}"
            parent_choices.append((parent.user.username, display_name))
        
        self.fields['parent_username'] = forms.ChoiceField(
            choices=parent_choices,
            widget=forms.Select(attrs={'class': 'form-control'}),
            label="Select Parent",
            help_text="Choose the parent from the list"
        )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
        label="Amount"
    )
    
    payment_method = forms.ChoiceField(
        choices=[('cash', 'Cash'), ('eftpos', 'EFTPOS')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Payment Method"
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes'}),
        label="Notes"
    )
    
    def clean_parent_username(self):
        username = self.cleaned_data['parent_username']
        
        if not username:
            raise ValidationError("Please select a parent from the dropdown.")
        
        # Find the parent by username
        try:
            user = User.objects.get(username=username)
            if not hasattr(user, 'parentprofile'):
                raise ValidationError("This user is not a registered parent.")
            
            parent_profile = user.parentprofile
            
            # Store the found parent profile for later use
            self._found_parent = parent_profile
            self._search_method = 'dropdown'
            
            return username
        except User.DoesNotExist:
            raise ValidationError(f"Parent not found with username '{username}'.")
    
    def get_parent_profile(self):
        """Get the found parent profile"""
        if hasattr(self, '_found_parent'):
            return self._found_parent
        return None
    
    def get_parent_and_children(self):
        """Get parent profile and children for manual sign-in"""
        if hasattr(self, '_found_parent'):
            parent_profile = self._found_parent
            children = parent_profile.children.all()
            return parent_profile, children
        else:
            raise ValidationError("No parent data available. Please search again.")
    
    def get_search_info(self):
        """Get information about how the parent was found"""
        if hasattr(self, '_found_parent') and hasattr(self, '_search_method'):
            return {
                'parent': self._found_parent,
                'method': self._search_method,
                'found_by': f"Selected from dropdown: {self._found_parent.last_name}, {self._found_parent.first_name}"
            }
        return None


class ManualSignInForm(forms.Form):
    """Form for staff to manually sign in children when parents forget QR codes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate parent choices
        parent_choices = [('', '--- Select a Parent ---')]
        parents = ParentProfile.objects.select_related('user').order_by('last_name', 'first_name')
        for parent in parents:
            display_name = f"{parent.last_name}, {parent.first_name} - {parent.user.username}"
            parent_choices.append((parent.user.username, display_name))
        
        self.fields['parent_username'] = forms.ChoiceField(
            choices=parent_choices,
            widget=forms.Select(attrs={'class': 'form-control'}),
            label="Select Parent",
            help_text="Choose the parent from the list"
        )
    
    def clean_parent_username(self):
        username = self.cleaned_data['parent_username']
        
        if not username:
            raise ValidationError("Please select a parent from the dropdown.")
        
        # Find the parent by username
        try:
            user = User.objects.get(username=username)
            if not hasattr(user, 'parentprofile'):
                raise ValidationError("This user is not a registered parent.")
            
            parent_profile = user.parentprofile
            
            # Check if parent has any children
            if not parent_profile.children.exists():
                raise ValidationError(f"Parent '{parent_profile.first_name} {parent_profile.last_name}' has no registered children.")
            
            # Store the found parent profile for later use
            self._found_parent = parent_profile
            self._search_method = 'dropdown'
            
            return username
        except User.DoesNotExist:
            raise ValidationError(f"Parent not found with username '{username}'.")
    
    def get_parent_and_children(self):
        """Get parent profile and children for manual sign-in"""
        if hasattr(self, '_found_parent'):
            parent_profile = self._found_parent
            children = parent_profile.children.all()
            return parent_profile, children
        else:
            raise ValidationError("No parent data available. Please search again.")
    
    def get_search_info(self):
        """Get information about how the parent was found"""
        if hasattr(self, '_found_parent') and hasattr(self, '_search_method'):
            return {
                'parent': self._found_parent,
                'method': self._search_method,
                'found_by': f"Selected from dropdown: {self._found_parent.last_name}, {self._found_parent.first_name}"
            }
        return None


# Welcomer System Forms

class ParentInteractionForm(forms.ModelForm):
    """Form for recording parent interactions by welcomers"""
    
    SEARCH_METHOD_CHOICES = [
        ('', 'Choose how to find this person...'),
        ('parent_search', 'Search by Parent Name'),
        ('child_search', 'Search by Child Name'),
        ('no_record', 'No Record Found - Manual Entry'),
    ]
    
    search_method = forms.ChoiceField(
        choices=SEARCH_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="How would you like to find this person?"
    )
    
    # Dynamic parent and child dropdowns (populated in __init__)
    parent_profile = forms.ModelChoiceField(
        queryset=ParentProfile.objects.none(),
        required=False,
        empty_label="--- Select a Parent ---",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Parent"
    )
    
    child_for_parent_lookup = forms.ModelChoiceField(
        queryset=Child.objects.none(),
        required=False,
        empty_label="--- Select a Child ---",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Child"
    )
    
    # Church attendance with conditional field
    attends_church = forms.ChoiceField(
        choices=[(None, '--- Not Asked ---'), (True, 'Yes'), (False, 'No')],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Do they currently attend a church?"
    )
    
    class Meta:
        model = ParentInteraction
        fields = [
            'search_method', 'parent_profile', 'child_for_parent_lookup',
            'manual_first_name', 'manual_last_name', 'manual_phone', 'manual_email', 
            'manual_address', 'manual_children_info',
            'conversation_team_member', 'interaction_day', 'attends_church', 'current_church', 'faith_status',
            'knows_lighthouse_members', 'previous_lighthouse_interaction',
            'interested_in_future_events', 'additional_notes'
        ]
        widgets = {
            'interaction_day': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'manual_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'manual_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'manual_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'manual_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'manual_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'manual_children_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'conversation_team_member': forms.TextInput(attrs={'class': 'form-control'}),
            'current_church': forms.TextInput(attrs={'class': 'form-control'}),
            'faith_status': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'knows_lighthouse_members': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'previous_lighthouse_interaction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'interested_in_future_events': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'additional_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'manual_first_name': 'First Name',
            'manual_last_name': 'Last Name',
            'manual_phone': 'Phone Number',
            'manual_email': 'Email Address',
            'manual_address': 'Address',
            'manual_children_info': 'Children Attending & Classes',
            'conversation_team_member': 'Team Member Who Had Conversation',
            'interaction_day': 'Which day did this conversation take place?',
            'current_church': 'Which church do they attend?',
            'faith_status': 'Current faith status',
            'knows_lighthouse_members': 'Do they know anyone from Lighthouse Church?',
            'previous_lighthouse_interaction': 'Have they interacted with Lighthouse Church before?',
            'interested_in_future_events': 'Interest in future events (Meet Jesus, services, community activities)',
            'additional_notes': 'Additional notes or observations',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate parent dropdown (sorted by last name)
        self.fields['parent_profile'].queryset = ParentProfile.objects.select_related('user').order_by('last_name', 'first_name')
        
        # Populate child dropdown - use queryset for ModelChoiceField
        self.fields['child_for_parent_lookup'].queryset = Child.objects.select_related('parent').order_by('first_name', 'last_name')
        
        # Set initial values for search method radio buttons
        if not self.instance.pk:
            self.fields['search_method'].initial = 'parent_search'
    
    def clean(self):
        cleaned_data = super().clean()
        search_method = cleaned_data.get('search_method')
        parent_profile = cleaned_data.get('parent_profile')
        child_for_parent_lookup = cleaned_data.get('child_for_parent_lookup')
        
        # Validation based on search method
        if search_method == 'parent_search':
            if not parent_profile:
                raise ValidationError("Please select a parent when using parent search.")
            # Clear manual fields
            for field in ['manual_first_name', 'manual_last_name', 'manual_phone', 
                         'manual_email', 'manual_address', 'manual_children_info']:
                cleaned_data[field] = ''
                
        elif search_method == 'child_search':
            if not child_for_parent_lookup:
                raise ValidationError("Please select a child when using child search.")
            # Set parent_profile based on selected child
            if child_for_parent_lookup:
                # child_for_parent_lookup is a Child instance from the ModelChoiceField
                cleaned_data['parent_profile'] = child_for_parent_lookup.parent
            # Clear manual fields
            for field in ['manual_first_name', 'manual_last_name', 'manual_phone', 
                         'manual_email', 'manual_address', 'manual_children_info']:
                cleaned_data[field] = ''
                
        elif search_method == 'no_record':
            # Clear linked parent
            cleaned_data['parent_profile'] = None
            # At least first name should be provided for manual entry
            if not cleaned_data.get('manual_first_name'):
                raise ValidationError("Please provide at least a first name for manual entries.")
        
        # Church attendance validation
        attends_church = cleaned_data.get('attends_church')
        current_church = cleaned_data.get('current_church')
        
        if attends_church == 'True' and not current_church:
            raise ValidationError("Please specify which church they attend.")
        elif attends_church == 'False':
            cleaned_data['current_church'] = ''  # Clear church name if they don't attend
        
        return cleaned_data


class PasswordChangeForm(forms.Form):
    """Form for changing user password"""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            # Check minimum length
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for at least one capital letter
            if not re.search(r'[A-Z]', password):
                raise ValidationError("Password must contain at least 1 capital letter (A-Z).")
            
            # Check for at least one number
            if not re.search(r'\d', password):
                raise ValidationError("Password must contain at least 1 number (0-9).")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("New passwords don't match.")
        
        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset via email"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email address'}),
        label="Email Address"
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            # Check if there's a parent profile with this email
            parent_profile = ParentProfile.objects.get(email=email)
            return email
        except ParentProfile.DoesNotExist:
            raise ValidationError("No account found with this email address. Please check your email or register a new account.")
