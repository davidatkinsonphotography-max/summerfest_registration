/**
 * Three Field Date Widget JavaScript
 * Handles validation, auto-advance, and user interaction
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeThreeFieldDateWidgets();
});

function initializeThreeFieldDateWidgets() {
    const widgets = document.querySelectorAll('.three-field-date-widget');
    
    widgets.forEach(widget => {
        const fieldName = widget.dataset.fieldName;
        const dayField = widget.querySelector('.three-field-date-day');
        const monthField = widget.querySelector('.three-field-date-month');
        const yearField = widget.querySelector('.three-field-date-year');
        const hiddenField = widget.querySelector(`input[name="${fieldName}"]`);
        const errorDiv = widget.querySelector(`#${fieldName}_error`);
        
        const fields = [dayField, monthField, yearField];
        
        // Auto-advance functionality
        fields.forEach((field, index) => {
            field.addEventListener('input', function(e) {
                // Only allow numeric input
                this.value = this.value.replace(/[^0-9]/g, '');
                
                // Auto-advance when field is full
                if (this.value.length === parseInt(this.maxLength) && fields[index + 1]) {
                    fields[index + 1].focus();
                }
                
                // Run validation on every change
                validateDate(fields, hiddenField, errorDiv);
            });
            
            // Handle backspace for better UX
            field.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && this.value === '' && index > 0) {
                    fields[index - 1].focus();
                }
            });
            
            // Handle paste events
            field.addEventListener('paste', function(e) {
                e.preventDefault();
                const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                handlePastedDate(pastedText, fields, hiddenField, errorDiv);
            });
        });
        
        // Initial validation if fields have values
        validateDate(fields, hiddenField, errorDiv);
    });
}

function validateDate(fields, hiddenField, errorDiv) {
    const [dayField, monthField, yearField] = fields;
    const day = dayField.value.trim();
    const month = monthField.value.trim();
    const year = yearField.value.trim();
    
    // Clear previous errors and reset styles
    clearErrors(fields, errorDiv);
    
    // Only validate when all fields are filled
    if (!day || !month || year.length < 4) {
        hiddenField.value = '';
        return false;
    }
    
    // Pad with zeros for validation
    const paddedDay = day.padStart(2, '0');
    const paddedMonth = month.padStart(2, '0');
    
    // Create date object for validation
    const testDate = new Date(`${year}-${paddedMonth}-${paddedDay}`);
    
    // Check if date is valid
    const isValidDate = testDate &&
        testDate.getFullYear() == year &&
        testDate.getMonth() + 1 == parseInt(month) &&
        testDate.getDate() == parseInt(day);
    
    if (!isValidDate) {
        showError(fields, errorDiv, 'Please enter a valid date of birth');
        hiddenField.value = '';
        return false;
    }
    
    // Range validation (2010-01-01 to today)
    const minDate = new Date('2010-01-01');
    const maxDate = new Date();
    maxDate.setHours(23, 59, 59, 999); // End of today
    
    if (testDate < minDate) {
        showError(fields, errorDiv, 'Date of birth cannot be before 1 January 2010');
        hiddenField.value = '';
        return false;
    }
    
    if (testDate > maxDate) {
        showError(fields, errorDiv, 'Date of birth cannot be in the future');
        hiddenField.value = '';
        return false;
    }
    
    // Success - clear errors and set hidden value
    clearErrors(fields, errorDiv);
    hiddenField.value = `${year}-${paddedMonth}-${paddedDay}`;
    return true;
}

function showError(fields, errorDiv, message) {
    fields.forEach(field => {
        field.style.borderColor = '#dc3545';
        field.classList.add('is-invalid');
    });
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.classList.add('d-block');
}

function clearErrors(fields, errorDiv) {
    fields.forEach(field => {
        field.style.borderColor = '';
        field.classList.remove('is-invalid');
    });
    errorDiv.textContent = '';
    errorDiv.style.display = 'none';
    errorDiv.classList.remove('d-block');
}

function handlePastedDate(pastedText, fields, hiddenField, errorDiv) {
    // Try to parse various date formats
    const [dayField, monthField, yearField] = fields;
    
    // Remove any non-digit characters and split
    const digits = pastedText.replace(/[^0-9]/g, '');
    
    if (digits.length === 8) {
        // Assume DDMMYYYY format
        const day = digits.substring(0, 2);
        const month = digits.substring(2, 4);
        const year = digits.substring(4, 8);
        
        dayField.value = day;
        monthField.value = month;
        yearField.value = year;
        
        validateDate(fields, hiddenField, errorDiv);
        return;
    }
    
    // Try to split by common separators
    const parts = pastedText.split(/[\/\-\.\s]+/);
    if (parts.length === 3) {
        // Determine if it's DD/MM/YYYY or MM/DD/YYYY or YYYY/MM/DD
        let day, month, year;
        
        if (parts[0].length === 4) {
            // YYYY-MM-DD format
            year = parts[0];
            month = parts[1];
            day = parts[2];
        } else if (parts[2].length === 4) {
            // DD/MM/YYYY or MM/DD/YYYY format
            // Assume DD/MM/YYYY for Australia
            day = parts[0];
            month = parts[1];
            year = parts[2];
        }
        
        if (day && month && year) {
            dayField.value = day;
            monthField.value = month;
            yearField.value = year;
            
            validateDate(fields, hiddenField, errorDiv);
        }
    }
}

// Export for use in other scripts if needed
window.validateThreeFieldDate = validateDate;
window.initializeThreeFieldDateWidgets = initializeThreeFieldDateWidgets;
