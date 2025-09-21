"""
Payment calculation service for Summerfest check-in system.
Implements per-check-in charging rules with Tuesday-Monday weeks and UTC+10 timezone.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Tuple, Dict, List
import pytz
from django.db import transaction
from django.db.models import Sum, Q
from .models import ParentProfile, Child, Attendance, PaymentTransaction

# Define timezone
AEST = pytz.timezone('Australia/Sydney')  # UTC+10 with DST handling

class PaymentCalculator:
    """Handles payment calculation for check-ins based on simplified rules.

    New logic:
    - Charge $6 per child per day (Wednesday–Saturday only)
    - Cap at 2 children per family per day ($12/day max)
    - Sunday is free
    - No weekly caps or thresholds
    """
    
    DAILY_CHILD_RATE = Decimal('6.00')
    DAILY_FAMILY_CAP = Decimal('12.00')  # Effectively 2 children max per day
    
    CHARGE_WEEKDAYS = {2, 3, 4, 5}  # Wed(2)–Sat(5) only
    
    @classmethod
    def get_current_aest_datetime(cls) -> datetime:
        """Get current datetime in AEST timezone."""
        return datetime.now(AEST)
    
    @classmethod
    def get_current_aest_date(cls) -> date:
        """Get current date in AEST timezone."""
        return cls.get_current_aest_datetime().date()
    
    @classmethod
    def get_week_boundaries(cls, check_date: date) -> Tuple[date, date]:
        """
        Legacy helper (not used by simplified rules). Keeping for compatibility with callers.
        """
        days_since_monday = check_date.weekday()
        week_start = check_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    @classmethod
    def get_daily_attendance_for_family(cls, parent_profile: ParentProfile, check_date: date) -> List[Attendance]:
        """Get all attendance records for a family on a specific date."""
        return Attendance.objects.filter(
            child__parent=parent_profile,
            date=check_date
        ).select_related('child')
    
    @classmethod
    def get_weekly_attendance_for_family(cls, parent_profile: ParentProfile, check_date: date) -> List[Attendance]:
        """Get all attendance records for a family in the current week."""
        week_start, week_end = cls.get_week_boundaries(check_date)
        
        return Attendance.objects.filter(
            child__parent=parent_profile,
            date__range=(week_start, week_end)
        ).select_related('child').order_by('date', 'time_in')
    
    @classmethod
    def get_daily_family_charge_total(cls, parent_profile: ParentProfile, check_date: date) -> Decimal:
        """Get total charges for a family on a specific date."""
        daily_attendance = cls.get_daily_attendance_for_family(parent_profile, check_date)
        return sum((attendance.charge_amount or Decimal('0.00')) for attendance in daily_attendance)
    
    @classmethod
    def count_weekly_signins_for_family(cls, parent_profile: ParentProfile, check_date: date) -> int:
        """Count total sign-ins for the family in the current week up to (but not including) check_date."""
        week_start, week_end = cls.get_week_boundaries(check_date)
        
        # Count unique child+date combinations up to but not including check_date
        weekly_attendance = Attendance.objects.filter(
            child__parent=parent_profile,
            date__range=(week_start, week_end),
            date__lt=check_date
        ).values('child_id', 'date').distinct()
        
        return weekly_attendance.count()
    
    @classmethod
    def has_child_checked_in_today(cls, child: Child, check_date: date) -> bool:
        """Check if a child has already checked in today."""
        return Attendance.objects.filter(
            child=child,
            date=check_date
        ).exists()
    
    @classmethod
    def calculate_charge_for_checkin(cls, child: Child, check_date: date = None) -> Tuple[Decimal, str]:
        """
        Calculate the charge for checking in a child under simplified rules.
        
        Returns:
            Tuple of (charge_amount, reason)
        """
        if check_date is None:
            check_date = cls.get_current_aest_date()

        parent_profile = child.parent

        # No double-charging per child per day
        if cls.has_child_checked_in_today(child, check_date):
            return Decimal('0.00'), 'Already checked in today'

        # Sunday is free; only charge Wed–Sat
        weekday = check_date.weekday()
        if weekday not in cls.CHARGE_WEEKDAYS:
            return Decimal('0.00'), 'No charge today'

        # Count how many charged children already today for this family
        daily_attendance = cls.get_daily_attendance_for_family(parent_profile, check_date)
        charged_count = sum(1 for att in daily_attendance if (att.charge_amount or Decimal('0.00')) > 0)

        if charged_count >= 2:
            return Decimal('0.00'), 'Daily family cap reached (2 children)'

        # Charge standard daily rate
        return cls.DAILY_CHILD_RATE, 'Standard daily rate (per child)'

    
    @classmethod
    @transaction.atomic
    def process_checkin_with_payment(cls, child: Child, check_date: date = None, 
                                   check_in_time: datetime = None) -> Tuple[Attendance, Decimal, str]:
        """
        Process check-in with payment calculation and balance update.
        
        Returns:
            Tuple of (attendance_record, charge_amount, charge_reason)
        """
        if check_date is None:
            check_date = cls.get_current_aest_date()
        
        if check_in_time is None:
            check_in_time = cls.get_current_aest_datetime()
        
        # Calculate charge
        charge_amount, charge_reason = cls.calculate_charge_for_checkin(child, check_date)
        
        # Create attendance record
        attendance = Attendance.objects.create(
            child=child,
            date=check_date,
            time_in=check_in_time,
            status='checked_in',
            charge_amount=charge_amount,
            charge_reason=charge_reason
        )
        
        # Update parent balance if there's a charge
        if charge_amount > 0:
            parent_profile = child.parent
            
            # Get or create payment account
            from .payment_views import get_or_create_payment_account
            payment_account = get_or_create_payment_account(parent_profile)
            
            # Deduct charge from payment account
            payment_account.balance -= charge_amount
            payment_account.save(update_fields=['balance'])
            
            # Create payment transaction record
            PaymentTransaction.objects.create(
                payment_account=payment_account,
                amount=-charge_amount,  # Negative for charge
                transaction_type='debit',
                description=f'Check-in charge for {child.first_name} {child.last_name} on {check_date}'
            )
            
            # Refresh the payment account to ensure we have the latest balance
            payment_account.refresh_from_db()
        
        return attendance, charge_amount, charge_reason
    
@classmethod
def get_family_weekly_summary(cls, parent_profile: ParentProfile, check_date: date = None) -> Dict:
    """Get a summary of family's weekly activity, charges, and weekly cap allowance."""
    if check_date is None:
        check_date = cls.get_current_aest_date()
    
    week_start, week_end = cls.get_week_boundaries(check_date)
    family_size = parent_profile.children.count()
    
    # Get weekly attendance
    weekly_attendance = cls.get_weekly_attendance_for_family(parent_profile, check_date)
    
    # Count unique sign-ins (child+date combinations)
    unique_signins = len(set(
        (att.child_id, att.date) for att in weekly_attendance
    ))
    
    # Total weekly charges
    weekly_charges = sum(att.charge_amount or Decimal('0.00') for att in weekly_attendance)
    
    # Determine how many children have attended this week
    children_attended = set(att.child_id for att in weekly_attendance)
    has_multiple_children_attended = len(children_attended) > 1 or family_size > 1
    
    # Weekly cap based on how many children have attended
    weekly_cap = Decimal('40.00') if has_multiple_children_attended else Decimal('20.00')
    
    # Remaining allowance
    remaining_allowance = max(Decimal('0.00'), weekly_cap - weekly_charges)
    
    # Next charge estimate
    next_charge, next_reason = cls.calculate_charge_for_checkin(
        parent_profile.children.first(), check_date
    ) if parent_profile.children.exists() else (Decimal('0.00'), 'No children')
    
    # Get current balance from payment account
    from .payment_views import get_or_create_payment_account
    payment_account = get_or_create_payment_account(parent_profile)
    
    return {
        'week_start': week_start,
        'week_end': week_end,
        'family_size': family_size,
        'unique_signins': unique_signins,
        'weekly_charges': weekly_charges,
        'weekly_cap': weekly_cap,
        'remaining_allowance': remaining_allowance,
        'next_charge_amount': next_charge,
        'next_charge_reason': next_reason,
        'current_balance': payment_account.balance,
        'threshold': cls.SINGLE_CHILD_THRESHOLD if family_size == 1 else cls.MULTI_CHILD_THRESHOLD
    }
