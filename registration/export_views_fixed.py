"""
Data export views for Summerfest registration system
Provides CSV/Excel exports for admin users
"""

import csv
from datetime import datetime
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Q
from .models import ParentProfile, Child, Attendance, PaymentAccount, PaymentTransaction, ParentInteraction

def is_staff_user(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_staff_user)
def export_dashboard(request):
    """Dashboard for data export options"""
    stats = {
        'total_families': ParentProfile.objects.count(),
        'total_children': Child.objects.count(),
        'total_attendance_records': Attendance.objects.count(),
        'total_payment_accounts': PaymentAccount.objects.count(),
        'total_transactions': PaymentTransaction.objects.count(),
        'total_conversations': ParentInteraction.objects.count(),
    }
    return render(request, 'admin/export_dashboard.html', {'stats': stats})


@login_required
@user_passes_test(is_staff_user)
def export_all_data_csv(request):
    """Export absolutely everything - comprehensive data report with all details"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="summerfest_COMPLETE_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Comprehensive header with absolutely everything
    writer.writerow([
        # Family/Parent Information
        'Family_ID',
        'Parent_Username',
        'Parent_First_Name',
        'Parent_Last_Name',
        'Parent_Email',
        'Parent_Phone',
        'Street_Address',
        'City',
        'Postcode',
        'How_Heard_About_Summerfest',
        'Additional_Information',
        'Attends_Church_Regularly',
        'Which_Church',
        'Emergency_Contact_Name',
        'Emergency_Contact_Phone',
        'Emergency_Contact_Relationship',
        'First_Aid_Consent',
        'Injury_Waiver',
        'Parent_Registration_Date',
        'Parent_Last_Updated',
        
        # Child Information
        'Child_ID',
        'Child_First_Name',
        'Child_Last_Name',
        'Child_Date_of_Birth',
        'Child_Age_Years',
        'Child_Gender',
        'Child_Class',
        'Has_Dietary_Needs',
        'Dietary_Needs_Detail',
        'Has_Medical_Needs',
        'Medical_Allergy_Details',
        'Photo_Consent',
        'Child_QR_Code_Manual_ID',
        'Child_Registration_Date',
        'Child_Last_Updated',
        
        # Attendance Summary
        'Total_Attendance_Days',
        'First_Checkin_Date',
        'Last_Checkin_Date',
        'Attendance_Details_All_Days',
        
        # Payment Information
        'Payment_Account_Balance',
        'Total_Amount_Paid',
        'Total_Amount_Charged',
        'Total_Transactions',
        'Payment_Account_Created',
        'All_Payment_Transactions',
        
        # Statistical Data
        'Days_Since_Registration',
        'Family_Total_Children',
        'Family_Total_Attendance_Records'
    ])
    
    # Get all comprehensive data
    for parent in ParentProfile.objects.select_related('user', 'payment_account').prefetch_related('children__attendance_records').all():
        payment_account = getattr(parent, 'payment_account', None)
        
        # Calculate payment totals
        total_paid = 0
        total_charged = 0
        total_transactions = 0
        payment_account_created = ''
        all_transactions_detail = ''
        
        if payment_account:
            credit_transactions = payment_account.transactions.filter(transaction_type='credit')
            debit_transactions = payment_account.transactions.filter(transaction_type='debit')
            total_paid = sum(t.amount for t in credit_transactions)
            total_charged = sum(abs(t.amount) for t in debit_transactions)
            total_transactions = payment_account.transactions.count()
            payment_account_created = payment_account.created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get all transaction details
            transactions = payment_account.transactions.order_by('created_at')
            transaction_details = []
            for t in transactions:
                transaction_details.append(
                    f"{t.created_at.strftime('%Y-%m-%d %H:%M')}:{t.transaction_type}:${t.amount}:{t.description or 'No description'}"
                )
            all_transactions_detail = ' | '.join(transaction_details)
        
        # Family statistics
        total_children = parent.children.count()
        family_attendance_records = Attendance.objects.filter(child__parent=parent).count()
        days_since_registration = (datetime.now().date() - parent.created_at.date()).days
        
        children = parent.children.all()
        if children:
            for child in children:
                # Calculate child age
                today = datetime.now().date()
                age = today.year - child.date_of_birth.year - ((today.month, today.day) < (child.date_of_birth.month, child.date_of_birth.day))
                
                # Get attendance details
                attendance_records = child.attendance_records.order_by('date', 'time_in')
                attendance_days = attendance_records.values('date').distinct().count()
                
                first_checkin = attendance_records.first()
                last_checkin = attendance_records.last()
                first_checkin_date = first_checkin.date.strftime('%Y-%m-%d') if first_checkin else 'Never'
                last_checkin_date = last_checkin.date.strftime('%Y-%m-%d') if last_checkin else 'Never'
                
                # Build detailed attendance string
                attendance_details = []
                for att in attendance_records:
                    time_in = att.time_in.strftime('%H:%M')
                    time_out = att.time_out.strftime('%H:%M') if att.time_out else 'Not checked out'
                    checked_in_by = att.checked_in_by.username if att.checked_in_by else 'Unknown'
                    checked_out_by = att.checked_out_by.username if att.checked_out_by else 'N/A'
                    charge = f"${att.charge_amount}" if hasattr(att, 'charge_amount') and att.charge_amount else '$0.00'
                    attendance_details.append(
                        f"{att.date.strftime('%Y-%m-%d')}({time_in}-{time_out},in_by:{checked_in_by},out_by:{checked_out_by},charge:{charge})"
                    )
                attendance_details_str = ' | '.join(attendance_details) if attendance_details else 'No attendance records'
                
                # QR Code manual ID
                qr_manual_id = f"summerfest_child_{child.qr_code_id}"
                
                writer.writerow([
                    # Family/Parent Information
                    parent.id,
                    parent.user.username,
                    parent.first_name,
                    parent.last_name,
                    parent.email,
                    parent.phone_number,
                    parent.street_address,
                    parent.city,
                    parent.postcode,
                    parent.get_how_heard_about_display(),
                    parent.additional_information or 'None',
                    'Yes' if parent.attends_church_regularly else 'No',
                    parent.which_church or 'None',
                    parent.emergency_contact_name,
                    parent.emergency_contact_phone,
                    parent.get_emergency_contact_relationship_display(),
                    'Yes' if parent.first_aid_consent else 'No',
                    'Yes' if parent.injury_waiver else 'No',
                    parent.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    parent.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    
                    # Child Information
                    child.id,
                    child.first_name,
                    child.last_name,
                    child.date_of_birth.strftime('%Y-%m-%d'),
                    age,
                    child.get_gender_display(),
                    child.get_child_class_display(),
                    'Yes' if child.has_dietary_needs else 'No',
                    child.dietary_needs_detail or 'None',
                    'Yes' if child.has_medical_needs else 'No',
                    child.medical_allergy_details or 'None',
                    'Yes' if child.photo_consent else 'No',
                    qr_manual_id,
                    child.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    child.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    
                    # Attendance Summary
                    attendance_days,
                    first_checkin_date,
                    last_checkin_date,
                    attendance_details_str,
                    
                    # Payment Information
                    f"${payment_account.balance}" if payment_account else '$0.00',
                    f"${total_paid}",
                    f"${total_charged}",
                    total_transactions,
                    payment_account_created,
                    all_transactions_detail or 'No transactions',
                    
                    # Statistical Data
                    days_since_registration,
                    total_children,
                    family_attendance_records
                ])
        else:
            # Parent with no children - still include parent data
            writer.writerow([
                # Family/Parent Information
                parent.id,
                parent.user.username,
                parent.first_name,
                parent.last_name,
                parent.email,
                parent.phone_number,
                parent.street_address,
                parent.city,
                parent.postcode,
                parent.get_how_heard_about_display(),
                parent.additional_information or 'None',
                'Yes' if parent.attends_church_regularly else 'No',
                parent.which_church or 'None',
                parent.emergency_contact_name,
                parent.emergency_contact_phone,
                parent.get_emergency_contact_relationship_display(),
                'Yes' if parent.first_aid_consent else 'No',
                'Yes' if parent.injury_waiver else 'No',
                parent.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                parent.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                
                # Child Information - Empty
                '',
                'NO CHILDREN REGISTERED',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                
                # Attendance Summary - Empty
                0,
                'Never',
                'Never',
                'No attendance records',
                
                # Payment Information
                f"${payment_account.balance}" if payment_account else '$0.00',
                f"${total_paid}",
                f"${total_charged}",
                total_transactions,
                payment_account_created,
                all_transactions_detail or 'No transactions',
                
                # Statistical Data
                days_since_registration,
                total_children,
                family_attendance_records
            ])
    
    return response


@login_required
@user_passes_test(is_staff_user)
def export_attendance_detailed_csv(request):
    """Export detailed attendance records with all check-in/out data"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="summerfest_attendance_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Attendance header
    writer.writerow([
        'Attendance_ID',
        'Date',
        'Child_First_Name',
        'Child_Last_Name',
        'Child_Class',
        'Parent_Name',
        'Parent_Phone',
        'Check_In_Time',
        'Check_Out_Time',
        'Total_Hours',
        'Checked_In_By_Staff',
        'Checked_Out_By_Staff',
        'Attendance_Status',
        'Charge_Amount',
        'Charge_Reason',
        'Notes',
        'Child_Dietary_Needs',
        'Child_Medical_Needs',
        'Photo_Consent'
    ])
    
    # Get all attendance records
    attendance_records = Attendance.objects.select_related(
        'child__parent',
        'checked_in_by',
        'checked_out_by'
    ).order_by('-date', '-time_in')
    
    for att in attendance_records:
        child = att.child
        parent = child.parent
        
        # Calculate total hours if checked out
        total_hours = ''
        if att.time_out:
            time_diff = att.time_out - att.time_in
            total_hours = f"{time_diff.total_seconds() / 3600:.1f} hours"
        else:
            total_hours = 'Still checked in'
        
        writer.writerow([
            att.id,
            att.date.strftime('%Y-%m-%d'),
            child.first_name,
            child.last_name,
            child.get_child_class_display(),
            f"{parent.first_name} {parent.last_name}",
            parent.phone_number,
            att.time_in.strftime('%H:%M:%S'),
            att.time_out.strftime('%H:%M:%S') if att.time_out else 'Not checked out',
            total_hours,
            att.checked_in_by.username if att.checked_in_by else 'Unknown',
            att.checked_out_by.username if att.checked_out_by else 'N/A',
            att.get_status_display(),
            f"${att.charge_amount}" if hasattr(att, 'charge_amount') and att.charge_amount else '$0.00',
            getattr(att, 'charge_reason', 'No reason recorded'),
            att.notes or 'No notes',
            child.dietary_needs_detail if child.has_dietary_needs else 'None',
            child.medical_allergy_details if child.has_medical_needs else 'None',
            'Yes' if child.photo_consent else 'No'
        ])
    
    return response


@login_required
@user_passes_test(is_staff_user)
def export_payments_detailed_csv(request):
    """Export detailed payment transactions and account information"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="summerfest_payments_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Payment transactions header
    writer.writerow([
        'Transaction_ID',
        'Parent_Name',
        'Parent_Username',
        'Parent_Email',
        'Parent_Phone',
        'Transaction_Date',
        'Transaction_Type',
        'Amount',
        'Description',
        'Payment_Method',
        'Reference',
        'Account_Balance_Now',
        'Processed_By',
        'Family_Total_Children',
        'Current_Account_Balance'
    ])
    
    # Get all payment transactions
    transactions = PaymentTransaction.objects.select_related(
        'payment_account__parent_profile__user'
    ).order_by('-created_at')
    
    for transaction in transactions:
        parent = transaction.payment_account.parent_profile
        total_children = parent.children.count()
        
        # Choose a sensible reference if available
        reference = (
            transaction.stripe_charge_id
            or transaction.stripe_payment_intent_id
            or ''
        )
        
        # Determine who processed/recorded the transaction
        processed_by = transaction.recorded_by.username if transaction.recorded_by else 'System'
        
        writer.writerow([
            transaction.id,
            f"{parent.first_name} {parent.last_name}",
            parent.user.username,
            parent.email,
            parent.phone_number,
            transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.transaction_type.upper(),
            f"${transaction.amount}",
            transaction.description or 'No description',
            transaction.payment_method or 'Unknown',
            reference or 'No reference',
            f"${transaction.payment_account.balance}",
            processed_by,
            total_children,
            f"${transaction.payment_account.balance}"
        ])
    
    return response


@login_required
@user_passes_test(is_staff_user)
def export_parent_conversations_csv(request):
    """Export all parent conversation interactions recorded by welcomers"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="summerfest_parent_conversations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Parent conversations header
    writer.writerow([
        'Conversation_ID',
        'Date_Recorded',
        'Interaction_Day',
        'Person_Type',  # Registered Parent or Manual Entry
        'Person_Name',
        'Phone_Number',
        'Email_Address',
        'Home_Address',
        'Children_Info',
        'Recorded_By_User',
        'Conversation_Team_Member',
        'Attends_Church',
        'Current_Church',
        'Faith_Status',
        'Knows_Lighthouse_Members',
        'Previous_Lighthouse_Interaction',
        'Interested_In_Future_Events',
        'Additional_Notes',
        'Search_Method',
        'Last_Updated'
    ])
    
    # Get all parent interactions with related data
    interactions = ParentInteraction.objects.select_related(
        'parent_profile__user',
        'welcomer__user'
    ).order_by('-created_at')
    
    for interaction in interactions:
        # Determine person type and details
        if interaction.parent_profile:
            person_type = 'Registered Parent'
            person_name = f"{interaction.parent_profile.first_name} {interaction.parent_profile.last_name}"
            phone_number = interaction.parent_profile.phone_number or ''
            email_address = interaction.parent_profile.email or ''
            home_address = f"{interaction.parent_profile.street_address}, {interaction.parent_profile.city} {interaction.parent_profile.postcode}".strip(', ')
            
            # Get children information
            children = interaction.parent_profile.children.all()
            if children:
                children_info = '; '.join([f"{child.first_name} {child.last_name} ({child.get_class_short_name()})" for child in children])
            else:
                children_info = 'No children registered'
        else:
            person_type = 'Manual Entry'
            person_name = f"{interaction.manual_first_name} {interaction.manual_last_name or ''}".strip()
            phone_number = interaction.manual_phone or ''
            email_address = interaction.manual_email or ''
            home_address = interaction.manual_address or ''
            children_info = interaction.manual_children_info or ''
        
        # Handle church attendance
        if interaction.attends_church is True:
            attends_church = 'Yes'
        elif interaction.attends_church is False:
            attends_church = 'No'
        else:
            attends_church = 'Not Asked'
        
        # Get who recorded vs who had the conversation
        recorded_by = interaction.welcomer.user.get_full_name() or interaction.welcomer.user.username
        conversation_team_member = interaction.conversation_team_member or recorded_by
        
        writer.writerow([
            interaction.id,
            interaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            interaction.get_interaction_day_display() if interaction.interaction_day else '',
            person_type,
            person_name,
            phone_number,
            email_address,
            home_address,
            children_info,
            recorded_by,
            conversation_team_member,
            attends_church,
            interaction.current_church or '',
            interaction.faith_status or '',
            interaction.knows_lighthouse_members or '',
            interaction.previous_lighthouse_interaction or '',
            interaction.interested_in_future_events or '',
            interaction.additional_notes or '',
            interaction.get_search_method_display(),
            interaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response
