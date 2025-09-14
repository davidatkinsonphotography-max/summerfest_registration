from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal
import re
from .models import ParentProfile, Child, PaymentTransaction


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
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
    
    AMOUNT_CHOICES = [
        ('6.00', '$6'),
        ('12.00', '$12'),
        ('18.00', '$18'),
        ('20.00', '$20'),
        ('40.00', '$40'),
        ('custom', 'Other Amount')
    ]
    
    amount_choice = forms.ChoiceField(
        choices=AMOUNT_CHOICES,
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
        if self.cleaned_data['amount_choice'] == 'custom':
            return self.cleaned_data['custom_amount']
        return Decimal(self.cleaned_data['amount_choice'])


class ManualPaymentForm(forms.Form):
    """Form for staff to record manual payments (cash/eftpos)"""
    
    search_type = forms.ChoiceField(
        choices=[
            ('username', 'Username'),
            ('surname', 'Surname'),
            ('phone', 'Phone Number'),
            ('qr', 'QR Code Scan')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='username',
        label="Search Type"
    )
    
    parent_search = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter search term'}),
        label="Find Parent",
        help_text="Search by username, surname, phone number, or scan QR code"
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
    
    def clean_parent_search(self):
        search_term = self.cleaned_data['parent_search'].strip()
        search_type = self.cleaned_data.get('search_type', 'username')
        
        if not search_term:
            raise ValidationError("Please enter a search term.")
        
        # Handle QR code search
        if search_type == 'qr':
            return self._search_by_qr_code(search_term)
        else:
            return self._search_by_parent_info(search_term, search_type)
    
    def _search_by_qr_code(self, qr_data):
        """Search parent by child's QR code"""
        # Check if it's a valid QR code format
        if not qr_data.startswith('summerfest_child_'):
            raise ValidationError("Invalid QR code format. QR codes should start with 'summerfest_child_'")
        
        try:
            uuid_part = qr_data.replace('summerfest_child_', '')
            child = Child.objects.get(qr_code_id=uuid_part)
            parent_profile = child.parent
            
            # Store found parent for later use
            self._found_parent = parent_profile
            self._search_method = 'qr_code'
            self._found_via_child = child
            
            return qr_data
        except Child.DoesNotExist:
            raise ValidationError("No child found with this QR code.")
    
    def _search_by_parent_info(self, search_term, search_type):
        """Search parent by username, surname, or phone number"""
        parent_profile = None
        
        if search_type == 'username':
            try:
                user = User.objects.get(username=search_term)
                if hasattr(user, 'parentprofile'):
                    parent_profile = user.parentprofile
                else:
                    raise ValidationError("This user is not a registered parent.")
            except User.DoesNotExist:
                raise ValidationError(f"No user found with username '{search_term}'.")
        
        elif search_type == 'surname':
            try:
                parent_profile = ParentProfile.objects.get(last_name__iexact=search_term)
            except ParentProfile.DoesNotExist:
                raise ValidationError(f"No parent found with surname '{search_term}'.")
            except ParentProfile.MultipleObjectsReturned:
                matching_parents = ParentProfile.objects.filter(last_name__iexact=search_term)
                usernames = [p.user.username for p in matching_parents[:5]]
                raise ValidationError(f"Multiple parents found with surname '{search_term}'. Use username search instead: {', '.join(usernames)}")
        
        elif search_type == 'phone':
            # Clean phone number (remove spaces, dashes, etc.)
            clean_phone = ''.join(filter(str.isdigit, search_term))
            if not clean_phone:
                raise ValidationError("Please enter a valid phone number.")
            
            try:
                parent_profile = ParentProfile.objects.get(phone_number=clean_phone)
            except ParentProfile.DoesNotExist:
                raise ValidationError(f"No parent found with phone number '{search_term}'.")
            except ParentProfile.MultipleObjectsReturned:
                raise ValidationError(f"Multiple parents found with phone number '{search_term}'. Please use a more specific search.")
        
        if parent_profile:
            # Store found parent for later use
            self._found_parent = parent_profile
            self._search_method = search_type
            
            return search_term
        else:
            raise ValidationError(f"No parent found matching '{search_term}'.")
    
    def get_parent_profile(self):
        """Get the found parent profile"""
        if hasattr(self, '_found_parent'):
            return self._found_parent
        return None
    
    def get_search_info(self):
        """Get information about how the parent was found"""
        if hasattr(self, '_found_parent') and hasattr(self, '_search_method'):
            found_by_mapping = {
                'username': f"Username: {self._found_parent.user.username}",
                'surname': f"Surname: {self._found_parent.last_name}",
                'phone': f"Phone: {self._found_parent.phone_number}",
                'qr_code': f"QR Code: {getattr(self, '_found_via_child', {}).first_name if hasattr(self, '_found_via_child') else 'N/A'}'s QR code"
            }
            
            return {
                'parent': self._found_parent,
                'method': self._search_method,
                'found_by': found_by_mapping.get(self._search_method, f"Method: {self._search_method}")
            }
        return None


class ManualSignInForm(forms.Form):
    """Form for staff to manually sign in children when parents forget QR codes"""
    
    search_type = forms.ChoiceField(
        choices=[
            ('parent', 'Search by Parent'),
            ('child', 'Search by Child Name')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='parent',
        label="Search Type"
    )
    
    search_query = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter search term'
        }),
        label="Search",
        help_text="Search by username, surname, phone number, or child name"
    )
    
    def clean_search_query(self):
        query = self.cleaned_data['search_query'].strip()
        search_type = self.cleaned_data.get('search_type', 'parent')
        
        if not query:
            raise ValidationError("Please enter a search term.")
        
        if search_type == 'child':
            return self._search_by_child_name(query)
        else:
            return self._search_by_parent(query)
    
    def _search_by_child_name(self, query):
        """Search for parent by child's name (case-insensitive, partial matches)"""
        # Find children with names containing the query (case-insensitive)
        children = Child.objects.filter(
            first_name__icontains=query
        ).select_related('parent').order_by('first_name', 'last_name')
        
        if not children.exists():
            raise ValidationError(f"No children found with name containing '{query}'. Try a different search term.")
        
        if children.count() == 1:
            # Only one child found - use their parent
            child = children.first()
            self._found_parent = child.parent
            self._search_method = 'child_name'
            self._matched_child = child
            return query
        else:
            # Multiple children found - provide selection options
            child_options = []
            for child in children[:10]:  # Limit to 10 results
                child_options.append(
                    f"{child.first_name} {child.last_name} (Parent: {child.parent.first_name} {child.parent.last_name}, Username: {child.parent.user.username})"
                )
            
            self._child_matches = children
            raise ValidationError(
                f"Multiple children found with name '{query}'. Please be more specific or use parent search with one of these usernames:\n\n" +
                "\n".join(child_options)
            )
    
    def _search_by_parent(self, query):
        """Search for parent by username, surname, or phone number"""
        # Try to find parent by different methods
        parent_profile = None
        search_method = None
        
        # Method 1: Search by username
        try:
            user = User.objects.get(username=query)
            if hasattr(user, 'parentprofile'):
                parent_profile = user.parentprofile
                search_method = 'username'
        except User.DoesNotExist:
            pass
        
        # Method 2: Search by surname (last_name)
        if not parent_profile:
            try:
                parent_profile = ParentProfile.objects.get(last_name__iexact=query)
                search_method = 'surname'
            except ParentProfile.DoesNotExist:
                pass
            except ParentProfile.MultipleObjectsReturned:
                # Multiple parents with same surname - provide helpful error
                matching_parents = ParentProfile.objects.filter(last_name__iexact=query)
                usernames = [p.user.username for p in matching_parents[:5]]  # Show up to 5
                raise ValidationError(f"Multiple families found with surname '{query}'. Try searching by username instead: {', '.join(usernames)}")
        
        # Method 3: Search by phone number
        if not parent_profile:
            # Clean phone number (remove spaces, dashes, etc.)
            clean_phone = ''.join(filter(str.isdigit, query))
            if clean_phone:
                try:
                    parent_profile = ParentProfile.objects.get(phone_number=clean_phone)
                    search_method = 'phone'
                except ParentProfile.DoesNotExist:
                    pass
                except ParentProfile.MultipleObjectsReturned:
                    raise ValidationError(f"Multiple parents found with phone number '{query}'. Please use a more specific search.")
        
        # If still not found, provide helpful error message
        if not parent_profile:
            raise ValidationError(f"No parent found matching '{query}'. Please check the username, surname, or phone number and try again.")
        
        # Check if parent has any children
        if not parent_profile.children.exists():
            raise ValidationError(f"Parent '{parent_profile.first_name} {parent_profile.last_name}' has no registered children.")
        
        # Store the found parent profile for later use
        self._found_parent = parent_profile
        self._search_method = search_method
        
        return query
    
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
            found_by_mapping = {
                'username': f"Username: {self._found_parent.user.username}",
                'surname': f"Surname: {self._found_parent.last_name}",
                'phone': f"Phone: {self._found_parent.phone_number}",
                'child_name': f"Child name: {getattr(self, '_matched_child', {}).first_name if hasattr(self, '_matched_child') else 'N/A'}"
            }
            
            return {
                'parent': self._found_parent,
                'method': self._search_method,
                'found_by': found_by_mapping.get(self._search_method, f"Method: {self._search_method}")
            }
        return None


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
