"""
Reports views for Summerfest registration system
Provides comprehensive analytics and reporting dashboards
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict, OrderedDict

from .models import (
    ParentProfile, Child, Attendance, PaymentTransaction, 
    PaymentAccount, ParentInteraction
)


def is_staff_user(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_staff_user)
def reports_dashboard(request):
    """Main reports dashboard with all analytics"""
    
    # Date range filter (default to last 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # 1. Children registered per class per day
    children_by_class_day = get_children_registered_by_class_day(start_date, end_date)
    
    # 2. Children checked in per class per day
    attendance_by_class_day = get_attendance_by_class_day(start_date, end_date)
    
    # 3. Where parents heard about Summerfest
    heard_about_stats = get_heard_about_summerfest_stats()
    
    # 4. Do parents attend church and where
    church_attendance_stats = get_church_attendance_stats()
    
    # 5. New registrations per day (parents and children)
    daily_registrations = get_daily_registrations(start_date, end_date)
    
    # 6. Income methods and amounts per day
    daily_income = get_daily_income(start_date, end_date)
    
    # 7. Overall summary statistics
    summary_stats = get_summary_statistics()
    
    # 8. Class enrollment summary
    class_enrollment = get_class_enrollment_summary()
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'children_by_class_day': children_by_class_day,
        'attendance_by_class_day': attendance_by_class_day,
        'heard_about_stats': heard_about_stats,
        'church_attendance_stats': church_attendance_stats,
        'daily_registrations': daily_registrations,
        'daily_income': daily_income,
        'summary_stats': summary_stats,
        'class_enrollment': class_enrollment,
        'date_range_days': (end_date - start_date).days + 1,
    }
    
    return render(request, 'registration/reports_dashboard.html', context)


def get_children_registered_by_class_day(start_date, end_date):
    """Get children registered per class per day"""
    children = Child.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).values(
        'created_at__date', 'child_class'
    ).annotate(
        count=Count('id')
    ).order_by('created_at__date', 'child_class')
    
    # Organize by date then class (using class codes as keys)
    result = defaultdict(lambda: {
        'creche': 0, 'tackers': 0, 'minis': 0, 'nitro': 0, '56ers': 0, 'total': 0
    })
    
    for item in children:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        class_code = item['child_class']  # Use the actual code (creche, tackers, etc.)
        count = item['count']
        result[date_str][class_code] = count
        result[date_str]['total'] += count
    
    return dict(result)


def get_attendance_by_class_day(start_date, end_date):
    """Get children checked in per class per day"""
    attendance = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('child').values(
        'date', 'child__child_class'
    ).annotate(
        count=Count('id')
    ).order_by('date', 'child__child_class')
    
    # Organize by date then class (using class codes as keys)
    result = defaultdict(lambda: {
        'creche': 0, 'tackers': 0, 'minis': 0, 'nitro': 0, '56ers': 0, 'total': 0
    })
    
    for item in attendance:
        date_str = item['date'].strftime('%Y-%m-%d')
        class_code = item['child__child_class']  # Use the actual code (creche, tackers, etc.)
        count = item['count']
        result[date_str][class_code] = count
        result[date_str]['total'] += count
    
    return dict(result)


def get_heard_about_summerfest_stats():
    """Get statistics on how parents heard about Summerfest"""
    heard_about = ParentProfile.objects.values(
        'how_heard_about'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get display names
    choices_dict = dict(ParentProfile.HEAR_ABOUT_CHOICES)
    result = []
    total = sum(item['count'] for item in heard_about)
    
    for item in heard_about:
        display_name = choices_dict.get(item['how_heard_about'], item['how_heard_about'])
        percentage = (item['count'] / total * 100) if total > 0 else 0
        result.append({
            'method': display_name,
            'count': item['count'],
            'percentage': round(percentage, 1)
        })
    
    return result


def get_church_attendance_stats():
    """Get church attendance statistics"""
    # Church attendance breakdown
    attendance_breakdown = ParentProfile.objects.aggregate(
        attends_church=Count('id', filter=Q(attends_church_regularly=True)),
        no_church=Count('id', filter=Q(attends_church_regularly=False)),
        total=Count('id')
    )
    
    # Specific churches
    churches = ParentProfile.objects.filter(
        attends_church_regularly=True,
        which_church__isnull=False
    ).exclude(which_church='').values(
        'which_church'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    return {
        'breakdown': attendance_breakdown,
        'churches': list(churches)
    }


def get_daily_registrations(start_date, end_date):
    """Get new registrations per day (parents and children)"""
    # Parent registrations by day
    parent_regs = ParentProfile.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).extra({
        'date': 'DATE(created_at)'
    }).values('date').annotate(
        parent_count=Count('id')
    ).order_by('date')
    
    # Children registrations by day
    child_regs = Child.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).extra({
        'date': 'DATE(created_at)'
    }).values('date').annotate(
        child_count=Count('id')
    ).order_by('date')
    
    # Combine data by date
    result = defaultdict(lambda: {'parents': 0, 'children': 0, 'total': 0})
    
    for item in parent_regs:
        date_str = item['date'].strftime('%Y-%m-%d') if hasattr(item['date'], 'strftime') else str(item['date'])
        result[date_str]['parents'] = item['parent_count']
    
    for item in child_regs:
        date_str = item['date'].strftime('%Y-%m-%d') if hasattr(item['date'], 'strftime') else str(item['date'])
        result[date_str]['children'] = item['child_count']
    
    # Calculate totals
    for date_str in result:
        result[date_str]['total'] = result[date_str]['parents'] + result[date_str]['children']
    
    return dict(result)


def get_daily_income(start_date, end_date):
    """Get income methods and amounts per day"""
    transactions = PaymentTransaction.objects.filter(
        created_at__date__range=[start_date, end_date],
        transaction_type='credit'  # Only income transactions
    ).values(
        'created_at__date', 'payment_method'
    ).annotate(
        total_amount=Sum('amount'),
        transaction_count=Count('id')
    ).order_by('created_at__date', 'payment_method')
    
    # Create a mapping from display names to template-safe keys
    method_key_mapping = {
        'Credit Card': 'credit_card',
        'Cash': 'cash',
        'EFTPOS': 'eftpos',
        'Bank Transfer': 'bank_transfer',
        'Other': 'other'
    }
    
    # Organize by date with all payment methods (using template-safe keys)
    result = defaultdict(lambda: {
        'credit_card': Decimal('0.00'),
        'cash': Decimal('0.00'), 
        'eftpos': Decimal('0.00'),
        'bank_transfer': Decimal('0.00'),
        'other': Decimal('0.00'),
        'total': Decimal('0.00')
    })
    
    for item in transactions:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        method = item['payment_method'] or 'Other'
        amount = item['total_amount'] or Decimal('0.00')
        
        # Convert method to template-safe key
        method_key = method_key_mapping.get(method, 'other')
        result[date_str][method_key] = amount
        result[date_str]['total'] += amount
    
    return dict(result)


def get_summary_statistics():
    """Get overall summary statistics"""
    return {
        'total_families': ParentProfile.objects.count(),
        'total_children': Child.objects.count(),
        'total_attendance_records': Attendance.objects.count(),
        'unique_attendance_days': Attendance.objects.values('date').distinct().count(),
        'total_revenue': PaymentTransaction.objects.filter(
            transaction_type='credit'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00'),
        'total_conversations': ParentInteraction.objects.count(),
        'active_payment_accounts': PaymentAccount.objects.filter(
            balance__gt=0
        ).count(),
    }


def get_class_enrollment_summary():
    """Get current class enrollment summary"""
    classes = Child.objects.values(
        'child_class'
    ).annotate(
        enrolled=Count('id')
    ).order_by('child_class')
    
    class_choices = dict(Child.CLASS_CHOICES)
    result = []
    
    for item in classes:
        result.append({
            'class_code': item['child_class'],
            'class_name': class_choices.get(item['child_class'], item['child_class']),
            'enrolled': item['enrolled']
        })
    
    return result
