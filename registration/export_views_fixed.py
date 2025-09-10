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
from .models import ParentProfile, Child, Attendance, PaymentAccount, PaymentTransaction, DailyAttendanceCharge

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
    }
    return render(request, 'admin/export_dashboard.html', {'stats': stats})


@login_required
@user_passes_test(is_staff_user)
def export_all_data_csv(request):
    """Export comprehensive data report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="summerfest_complete_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Family ID',
        'Parent Username',
        'Parent Name',
        'Email',
        'Phone',
        'Address',
        'Church',
        'Child ID',
        'Child Name',
        'Child DOB',
        'Child Age',
        'Child Class',
        'Dietary Needs',
        'Medical Needs',
        'Total Attendance Days',
        'Account Balance',
        'Total Paid',
        'Total Charged'
    ])
    
    # Write comprehensive data
    for parent in ParentProfile.objects.select_related('user', 'payment_account').prefetch_related('children').all():
        payment_account = getattr(parent, 'payment_account', None)
        total_paid = 0
        total_charged = 0
        
        if payment_account:
            credit_transactions = payment_account.transactions.filter(transaction_type='credit')
            debit_transactions = payment_account.transactions.filter(transaction_type='debit')
            total_paid = sum(t.amount for t in credit_transactions)
            total_charged = sum(abs(t.amount) for t in debit_transactions)
        
        children = parent.children.all()
        if children:
            for child in children:
                # Calculate age
                today = datetime.now().date()
                age = today.year - child.date_of_birth.year - ((today.month, today.day) < (child.date_of_birth.month, child.date_of_birth.day))
                
                # Get attendance count
                attendance_days = child.attendance_records.values('date').distinct().count()
                
                writer.writerow([
                    parent.id,
                    parent.user.username,
                    f"{parent.first_name} {parent.last_name}",
                    parent.email,
                    parent.phone_number,
                    f"{parent.street_address}, {parent.city} {parent.postcode}",
                    parent.which_church if parent.attends_church_regularly else 'No church',
                    child.id,
                    f"{child.first_name} {child.last_name}",
                    child.date_of_birth.strftime('%Y-%m-%d'),
                    age,
                    child.get_child_class_display(),
                    child.dietary_needs_detail if child.has_dietary_needs else 'None',
                    child.medical_allergy_details if child.has_medical_needs else 'None',
                    attendance_days,
                    payment_account.balance if payment_account else '0.00',
                    total_paid,
                    total_charged
                ])
        else:
            # Parent with no children
            writer.writerow([
                parent.id,
                parent.user.username,
                f"{parent.first_name} {parent.last_name}",
                parent.email,
                parent.phone_number,
                f"{parent.street_address}, {parent.city} {parent.postcode}",
                parent.which_church if parent.attends_church_regularly else 'No church',
                '',
                'No children registered',
                '',
                '',
                '',
                '',
                '',
                0,
                payment_account.balance if payment_account else '0.00',
                total_paid,
                total_charged
            ])
    
    return response
