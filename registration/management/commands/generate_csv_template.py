"""
Django management command to generate CSV template for importing previous year data.

Usage:
    python manage.py generate_csv_template > import_template.csv
    python manage.py generate_csv_template --with-sample-data > sample_data.csv
"""

import csv
import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate CSV template for importing previous year data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-sample-data',
            action='store_true',
            help='Include sample data rows',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: stdout)',
        )

    def handle(self, *args, **options):
        """Generate CSV template"""
        headers = self.get_csv_headers()
        
        output_file = sys.stdout
        if options['output']:
            output_file = open(options['output'], 'w', newline='', encoding='utf-8')
        
        try:
            writer = csv.writer(output_file)
            
            # Write headers
            writer.writerow(headers)
            
            # Write sample data if requested
            if options['with_sample_data']:
                sample_rows = self.get_sample_data()
                for row in sample_rows:
                    writer.writerow(row)
                    
            if options['output']:
                self.stdout.write(self.style.SUCCESS(f'CSV template written to: {options["output"]}'))
            else:
                self.stderr.write('CSV template written to stdout')
                
        finally:
            if options['output']:
                output_file.close()

    def get_csv_headers(self):
        """Get CSV headers in correct order"""
        return [
            # Parent identification (REQUIRED)
            'parent_username',
            'temp_password',
            'parent_first_name',
            'parent_last_name', 
            'parent_email',
            
            # Parent contact details (OPTIONAL)
            'phone_number',
            'street_address',
            'city',
            'postcode',
            
            # Parent background (OPTIONAL)
            'how_heard_about',
            'additional_information',
            'attends_church_regularly',
            'which_church',
            
            # Emergency contact (OPTIONAL)
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            
            # Consents (OPTIONAL - defaults to True)
            'first_aid_consent',
            'injury_waiver',
            
            # Account info (OPTIONAL)
            'account_balance',
            
            # Child information (REQUIRED)
            'child_first_name',
            'child_last_name',
            'child_date_of_birth',
            'child_gender',
            'child_class',
            
            # Child details (OPTIONAL)
            'has_dietary_needs',
            'dietary_needs_detail',
            'has_medical_needs',
            'medical_allergy_details',
            'photo_consent',
        ]

    def get_sample_data(self):
        """Get sample data rows for testing"""
        return [
            # Sample row 1 - Family with 2 children
            [
                'smith.family', 'TempPass123', 'John', 'Smith', 'john.smith@email.com',
                '0412345678', '123 Main Street', 'Brisbane', '4000',
                'friend', 'Looking forward to Summerfest!', 'True', 'Lighthouse Church',
                'Jane Smith', '0412345679', 'spouse',
                'True', 'True', '50.00',
                'Emma', 'Smith', '15/06/2018', 'female', 'minis',
                'True', 'Gluten free diet', 'False', '', 'True'
            ],
            [
                'smith.family', 'TempPass123', 'John', 'Smith', 'john.smith@email.com',
                '0412345678', '123 Main Street', 'Brisbane', '4000',
                'friend', 'Looking forward to Summerfest!', 'True', 'Lighthouse Church',
                'Jane Smith', '0412345679', 'spouse',
                'True', 'True', '', # Empty balance for second child
                'Oliver', 'Smith', '22/03/2020', 'male', 'tackers',
                'False', '', 'True', 'Asthma - has inhaler', 'True'
            ],
            # Sample row 2 - Single parent
            [
                'jones.sarah', 'SecurePass456', 'Sarah', 'Jones', 'sarah.jones@email.com',
                '0423456789', '456 Oak Avenue', 'Melbourne', '3000',
                'facebook', '', 'False', '',
                'Michael Jones', '0423456790', 'grandparent',
                'True', 'True', '25.00',
                'Lily', 'Jones', '08/11/2017', 'female', 'nitro',
                'False', '', 'False', '', 'False'
            ],
        ]
