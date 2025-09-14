from django import forms
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from datetime import datetime, date
import re


class ThreeFieldDateWidget(Widget):
    """
    A widget that displays three separate text inputs for day, month, and year.
    More mobile-friendly than date pickers.
    """
    
    template_name = 'registration/widgets/three_field_date.html'
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs = attrs or {}
    
    def format_value(self, value):
        """Format the date value for display in the widget"""
        if value is None:
            return {'day': '', 'month': '', 'year': ''}
        
        if isinstance(value, str):
            # Try to parse the string date
            try:
                if re.match(r'\d{4}-\d{2}-\d{2}', value):
                    # ISO format YYYY-MM-DD
                    year, month, day = value.split('-')
                    return {
                        'day': str(int(day)),
                        'month': str(int(month)),
                        'year': year
                    }
            except (ValueError, AttributeError):
                pass
            return {'day': '', 'month': '', 'year': ''}
        
        if isinstance(value, (date, datetime)):
            return {
                'day': str(value.day),
                'month': str(value.month),
                'year': str(value.year)
            }
        
        return {'day': '', 'month': '', 'year': ''}
    
    def value_from_datadict(self, data, files, name):
        """Extract the date value from the form data"""
        day = data.get(f'{name}_day', '').strip()
        month = data.get(f'{name}_month', '').strip()
        year = data.get(f'{name}_year', '').strip()
        
        # Return None if any field is empty
        if not day or not month or not year:
            return None
        
        try:
            # Pad day and month with leading zeros
            day = day.zfill(2)
            month = month.zfill(2)
            
            # Construct ISO date string
            date_str = f'{year}-{month}-{day}'
            
            # Validate by parsing
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Return as ISO string for Django to handle
            return date_str
            
        except (ValueError, TypeError):
            # Return the invalid data so Django's validation can catch it
            return f'{day}/{month}/{year}'
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget HTML"""
        if attrs is None:
            attrs = {}
        
        attrs.update(self.attrs)
        formatted_value = self.format_value(value)
        
        # Generate unique IDs for each field
        day_id = f'{name}_day'
        month_id = f'{name}_month'  
        year_id = f'{name}_year'
        hidden_id = name
        error_id = f'{name}_error'
        
        html = f'''
        <div class="three-field-date-widget" data-field-name="{name}">
            <div class="d-flex gap-2 align-items-center">
                <div class="flex-shrink-0">
                    <input type="text" 
                           id="{day_id}" 
                           name="{day_id}"
                           class="form-control text-center three-field-date-day" 
                           maxlength="2" 
                           placeholder="DD" 
                           style="width: 60px;"
                           value="{formatted_value['day']}"
                           inputmode="numeric"
                           pattern="[0-9]*">
                </div>
                <div class="flex-shrink-0">
                    <span class="text-muted">/</span>
                </div>
                <div class="flex-shrink-0">
                    <input type="text" 
                           id="{month_id}" 
                           name="{month_id}"
                           class="form-control text-center three-field-date-month" 
                           maxlength="2" 
                           placeholder="MM" 
                           style="width: 60px;"
                           value="{formatted_value['month']}"
                           inputmode="numeric"
                           pattern="[0-9]*">
                </div>
                <div class="flex-shrink-0">
                    <span class="text-muted">/</span>
                </div>
                <div class="flex-shrink-0">
                    <input type="text" 
                           id="{year_id}" 
                           name="{year_id}"
                           class="form-control text-center three-field-date-year" 
                           maxlength="4" 
                           placeholder="YYYY" 
                           style="width: 80px;"
                           value="{formatted_value['year']}"
                           inputmode="numeric"
                           pattern="[0-9]*">
                </div>
            </div>
            <input type="hidden" id="{hidden_id}" name="{name}">
            <div id="{error_id}" class="invalid-feedback" style="display: none;"></div>
        </div>
        '''
        
        return mark_safe(html)
    
    class Media:
        js = ('registration/js/three_field_date_widget.js',)
        css = {
            'all': ('registration/css/three_field_date_widget.css',)
        }


class ThreeFieldDateField(forms.DateField):
    """
    A DateField that uses the ThreeFieldDateWidget
    """
    
    widget = ThreeFieldDateWidget
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', ThreeFieldDateWidget())
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """Convert the field value to a Python date object"""
        if value in self.empty_values:
            return None
        
        if isinstance(value, (date, datetime)):
            return value if isinstance(value, date) else value.date()
        
        if isinstance(value, str):
            # Handle the DD/MM/YYYY format that might come from invalid data
            if '/' in value:
                try:
                    parts = value.split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        value = f'{year}-{month.zfill(2)}-{day.zfill(2)}'
                except (ValueError, IndexError):
                    raise forms.ValidationError('Enter a valid date.')
            
            # Try to parse ISO format
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise forms.ValidationError('Enter a valid date.')
        
        raise forms.ValidationError('Enter a valid date.')
    
    def validate(self, value):
        """Validate the date value"""
        super().validate(value)
        
        if value is not None:
            # Additional validation for reasonable date ranges
            min_date = date(2010, 1, 1)
            max_date = date.today()
            
            if value < min_date:
                raise forms.ValidationError(f'Date of birth cannot be before {min_date.strftime("%d/%m/%Y")}.')
            
            if value > max_date:
                raise forms.ValidationError('Date of birth cannot be in the future.')
