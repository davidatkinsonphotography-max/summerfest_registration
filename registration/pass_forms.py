"""
Forms for the pass purchase system
"""
from django import forms
from datetime import date, timedelta
from .models import Pass

class PurchasePassForm(forms.Form):
    """Form for purchasing passes"""
    
    PASS_CHOICES = [
        ('daily_child', 'Daily Child Pass - $6 (Valid for one day, one child)'),
        ('daily_family', 'Daily Family Pass - $12 (Valid for one day, unlimited children)'),
        ('weekly_child', 'Weekly Child Pass - $20 (Valid for 5 days, one child)'),
        ('weekly_family', 'Weekly Family Pass - $40 (Valid for 5 days, unlimited children)'),
    ]
    
    pass_type = forms.ChoiceField(
        choices=PASS_CHOICES,
        widget=forms.RadioSelect,
        label="Select Pass Type"
    )
    
    start_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()}),
        label="Start Date",
        help_text="When should this pass become valid?"
    )
    
    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date < date.today():
            raise forms.ValidationError("Start date cannot be in the past")
        return start_date
    
    def get_end_date(self):
        """Calculate end date based on pass type and start date"""
        start_date = self.cleaned_data.get('start_date')
        pass_type = self.cleaned_data.get('pass_type')
        
        if not start_date or not pass_type:
            return None
            
        if pass_type.startswith('daily_'):
            return start_date  # Daily passes are valid for just one day
        elif pass_type.startswith('weekly_'):
            # Weekly passes are valid for 5 weekdays (Monday-Friday)
            # Find the end of the week (Friday) from start date
            days_until_friday = (4 - start_date.weekday()) % 7
            if start_date.weekday() > 4:  # If starting on weekend, move to next Monday
                days_until_monday = (7 - start_date.weekday()) % 7
                start_date = start_date + timedelta(days=days_until_monday)
                return start_date + timedelta(days=4)  # Monday + 4 = Friday
            return start_date + timedelta(days=days_until_friday)
    
    def get_price(self):
        """Get the price for the selected pass type"""
        pass_type = self.cleaned_data.get('pass_type')
        if pass_type:
            return Pass.PASS_PRICES.get(pass_type, 0)
        return 0
