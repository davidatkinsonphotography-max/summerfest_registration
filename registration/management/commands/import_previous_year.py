"""
Django management command to import previous year Summerfest data from CSV files.

Usage:
    python manage.py import_previous_year --parents parents.csv --children children.csv
    python manage.py import_previous_year --combined combined.csv
    python manage.py import_previous_year --dry-run parents.csv children.csv
"""

import csv
import sys
from datetime import datetime, date
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.crypto import get_random_string

from registration.models import ParentProfile, Child, PaymentAccount


class Command(BaseCommand):
    help = 'Import previous year Summerfest data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--parents',
            type=str,
            help='CSV file containing parent data',
        )
        parser.add_argument(
            '--children',
            type=str,
            help='CSV file containing children data',
        )
        parser.add_argument(
            '--combined',
            type=str,
            help='CSV file containing combined parent and child data (one row per child)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually importing data (validation only)',
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Skip creating user accounts (useful for testing)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        if not any([options['parents'], options['children'], options['combined']]):
            raise CommandError('You must specify either --parents and --children, or --combined')

        if options['combined']:
            self.import_combined_csv(options['combined'], options['dry_run'], options['skip_users'])
        else:
            if not (options['parents'] and options['children']):
                raise CommandError('When using separate files, you must specify both --parents and --children')
            self.import_separate_csv(options['parents'], options['children'], options['dry_run'], options['skip_users'])

    def import_combined_csv(self, csv_file, dry_run=False, skip_users=False):
        """Import from combined CSV (one row per child with parent info repeated)"""
        self.stdout.write(f'Importing from combined CSV: {csv_file}')
        
        parents_created = {}
        children_created = 0
        errors = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                # Validate headers
                required_headers = self.get_required_combined_headers()
                missing_headers = [h for h in required_headers if h not in reader.fieldnames]
                if missing_headers:
                    raise CommandError(f'Missing required headers: {missing_headers}')
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be imported'))
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, 1):
                        try:
                            # Process parent (create if not exists)
                            parent_key = row['parent_username'].strip().lower()
                            if parent_key not in parents_created:
                                parent_profile = self.create_parent_from_row(row, dry_run, skip_users)
                                if not dry_run:
                                    parents_created[parent_key] = parent_profile
                                else:
                                    parents_created[parent_key] = f"DRY_RUN_PARENT_{parent_key}"
                            
                            # Process child
                            if not dry_run:
                                parent_profile = parents_created[parent_key]
                                self.create_child_from_row(row, parent_profile)
                            
                            children_created += 1
                            
                            if row_num % 10 == 0:
                                self.stdout.write(f'Processed {row_num} rows...')
                                
                        except Exception as e:
                            error_msg = f'Row {row_num}: {str(e)}'
                            errors.append(error_msg)
                            self.stdout.write(self.style.ERROR(error_msg))
                            continue
                    
                    if dry_run:
                        raise transaction.TransactionManagementError("Dry run - rolling back")
                        
        except transaction.TransactionManagementError:
            if not dry_run:
                raise
            
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'Import {"simulation" if dry_run else "completed"}:\n'
            f'  - Parents: {len(parents_created)}\n'
            f'  - Children: {children_created}\n'
            f'  - Errors: {len(errors)}'
        ))
        
        if errors:
            self.stdout.write(self.style.ERROR('Errors encountered:'))
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(f'  {error}')
            if len(errors) > 10:
                self.stdout.write(f'  ... and {len(errors) - 10} more errors')

    def create_parent_from_row(self, row, dry_run=False, skip_users=False):
        """Create parent profile from CSV row"""
        username = row['parent_username'].strip()
        temp_password = row.get('temp_password', '').strip()
        
        if not temp_password:
            temp_password = get_random_string(12)
        
        if dry_run:
            self.stdout.write(f'Would create parent: {username}')
            return None
        
        # Create user account
        if not skip_users:
            if User.objects.filter(username=username).exists():
                raise ValueError(f'Username {username} already exists')
            
            user = User.objects.create_user(
                username=username,
                email=row['parent_email'].strip(),
                password=temp_password,
                first_name=row['parent_first_name'].strip(),
                last_name=row['parent_last_name'].strip(),
            )
        else:
            # For testing - create a dummy user
            user = User(username=username)
            user.save()
        
        # Create parent profile
        parent_profile = ParentProfile.objects.create(
            user=user,
            first_name=row['parent_first_name'].strip(),
            last_name=row['parent_last_name'].strip(),
            street_address=row.get('street_address', '').strip(),
            city=row.get('city', '').strip(),
            postcode=row.get('postcode', '').strip(),
            email=row['parent_email'].strip(),
            phone_number=row.get('phone_number', '').strip(),
            how_heard_about=row.get('how_heard_about', 'friend').strip(),
            additional_information=row.get('additional_information', '').strip(),
            attends_church_regularly=self.parse_boolean(row.get('attends_church_regularly', 'False')),
            which_church=row.get('which_church', '').strip(),
            emergency_contact_name=row.get('emergency_contact_name', '').strip(),
            emergency_contact_phone=row.get('emergency_contact_phone', '').strip(),
            emergency_contact_relationship=row.get('emergency_contact_relationship', 'parent').strip(),
            first_aid_consent=self.parse_boolean(row.get('first_aid_consent', 'True')),
            injury_waiver=self.parse_boolean(row.get('injury_waiver', 'True')),
        )
        
        # Create payment account
        PaymentAccount.objects.create(
            parent_profile=parent_profile,
            balance=Decimal(row.get('account_balance', '0.00'))
        )
        
        return parent_profile

    def create_child_from_row(self, row, parent_profile):
        """Create child from CSV row"""
        # Parse date of birth
        dob_str = row['child_date_of_birth'].strip()
        try:
            if '/' in dob_str:
                child_dob = datetime.strptime(dob_str, '%d/%m/%Y').date()
            elif '-' in dob_str:
                child_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            else:
                raise ValueError(f'Invalid date format: {dob_str}')
        except ValueError as e:
            raise ValueError(f'Error parsing child date of birth "{dob_str}": {str(e)}')
        
        child = Child.objects.create(
            parent=parent_profile,
            first_name=row['child_first_name'].strip(),
            last_name=row['child_last_name'].strip(),
            date_of_birth=child_dob,
            gender=row.get('child_gender', 'male').strip().lower(),
            child_class=row['child_class'].strip().lower(),
            has_dietary_needs=self.parse_boolean(row.get('has_dietary_needs', 'False')),
            dietary_needs_detail=row.get('dietary_needs_detail', '').strip(),
            has_medical_needs=self.parse_boolean(row.get('has_medical_needs', 'False')),
            medical_allergy_details=row.get('medical_allergy_details', '').strip(),
            photo_consent=self.parse_boolean(row.get('photo_consent', 'True')),
        )
        
        return child

    def parse_boolean(self, value):
        """Parse various boolean representations"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ['true', '1', 'yes', 'y', 'on']
        return False

    def get_required_combined_headers(self):
        """Get list of required CSV headers for combined import"""
        return [
            # Parent identification
            'parent_username',
            'temp_password',
            'parent_first_name',
            'parent_last_name',
            'parent_email',
            
            # Child required fields
            'child_first_name',
            'child_last_name',
            'child_date_of_birth',
            'child_class',
        ]

    def import_separate_csv(self, parents_file, children_file, dry_run=False, skip_users=False):
        """Import from separate parent and children CSV files"""
        self.stdout.write('Separate CSV import not implemented yet.')
        self.stdout.write('Please use the combined CSV format for now.')
        raise CommandError('Use --combined option instead')

    def print_csv_template(self):
        """Print CSV template to stdout"""
        headers = self.get_all_csv_headers()
        self.stdout.write('CSV Headers (copy this line to your CSV file):')
        self.stdout.write(','.join(headers))

    def get_all_csv_headers(self):
        """Get all possible CSV headers with descriptions"""
        return [
            # Parent identification (REQUIRED)
            'parent_username',           # Unique username for login
            'temp_password',             # Temporary password you assign
            'parent_first_name',         # Parent first name (REQUIRED)
            'parent_last_name',          # Parent last name (REQUIRED)
            'parent_email',              # Parent email address (REQUIRED)
            
            # Parent contact details (OPTIONAL)
            'phone_number',              # Phone number
            'street_address',            # Street address
            'city',                      # City
            'postcode',                  # Postcode/ZIP
            
            # Parent background (OPTIONAL)
            'how_heard_about',           # How they heard about Summerfest
            'additional_information',    # Any additional info
            'attends_church_regularly',  # True/False
            'which_church',              # Church name if they attend
            
            # Emergency contact (OPTIONAL)
            'emergency_contact_name',         # Emergency contact name
            'emergency_contact_phone',        # Emergency contact phone
            'emergency_contact_relationship', # Relationship to child
            
            # Consents (OPTIONAL - defaults to True)
            'first_aid_consent',         # True/False - consent for first aid
            'injury_waiver',             # True/False - injury waiver signed
            
            # Account info (OPTIONAL)
            'account_balance',           # Starting account balance (e.g., "25.00")
            
            # Child information (REQUIRED)
            'child_first_name',          # Child first name (REQUIRED)
            'child_last_name',           # Child last name (REQUIRED)
            'child_date_of_birth',       # Date in DD/MM/YYYY or YYYY-MM-DD format (REQUIRED)
            'child_gender',              # male/female (REQUIRED)
            'child_class',               # creche/tackers/minis/nitro/56ers (REQUIRED)
            
            # Child details (OPTIONAL)
            'has_dietary_needs',         # True/False
            'dietary_needs_detail',      # Details if has dietary needs
            'has_medical_needs',         # True/False
            'medical_allergy_details',   # Details if has medical needs
            'photo_consent',             # True/False - consent for photos
        ]
