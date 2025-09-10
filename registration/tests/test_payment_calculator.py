"""
Tests for PaymentCalculator functionality
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal

from registration.models import ParentProfile, Child, Attendance
from registration.payment_calculator import PaymentCalculator


class PaymentCalculatorTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user and parent
        self.user = User.objects.create_user(
            username='testparent',
            email='test@example.com',
            password='testpass123'
        )
        self.parent = ParentProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Parent',
            street_address='123 Test St',
            city='Test City',
            postcode='12345',
            email='test@example.com',
            phone_number='+61412345678',
            how_heard_about='other',
            attends_church_regularly=False,
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+61412345679',
            emergency_contact_relationship='parent',
            first_aid_consent=True,
            injury_waiver=True
        )
        
        # Create test children
        self.child1 = Child.objects.create(
            parent=self.parent,
            first_name='Child',
            last_name='One',
            date_of_birth=date(2015, 1, 1),
            gender='boy',
            child_class='K-2'
        )
        
        self.child2 = Child.objects.create(
            parent=self.parent,
            first_name='Child',
            last_name='Two', 
            date_of_birth=date(2017, 1, 1),
            gender='girl',
            child_class='K-2'
        )

    def test_timezone_handling(self):
        """Test AEST timezone handling"""
        aest_datetime = PaymentCalculator.get_current_aest_datetime()
        aest_date = PaymentCalculator.get_current_aest_date()
        
        self.assertIsNotNone(aest_datetime.tzinfo)
        self.assertIsInstance(aest_date, date)
        
        # Should be AEST/AEDT timezone
        tz_name = str(aest_datetime.tzinfo)
        self.assertIn('Australia/Sydney', tz_name)

    def test_week_boundaries_tuesday_monday(self):
        """Test that weeks run Tuesday to Monday"""
        test_cases = [
            # (date, expected_week_start, expected_week_end)
            (date(2025, 1, 6), date(2024, 12, 31), date(2025, 1, 6)),   # Monday -> prev Tue to this Mon
            (date(2025, 1, 7), date(2025, 1, 7), date(2025, 1, 13)),    # Tuesday -> this Tue to next Mon
            (date(2025, 1, 8), date(2025, 1, 7), date(2025, 1, 13)),    # Wednesday -> this week
            (date(2025, 1, 13), date(2025, 1, 7), date(2025, 1, 13)),   # Monday -> this week
        ]
        
        for test_date, expected_start, expected_end in test_cases:
            week_start, week_end = PaymentCalculator.get_week_boundaries(test_date)
            self.assertEqual(week_start, expected_start, 
                           f"Week start for {test_date} ({test_date.strftime('%A')})")
            self.assertEqual(week_end, expected_end,
                           f"Week end for {test_date} ({test_date.strftime('%A')})")

    def test_single_child_pricing(self):
        """Test pricing for single child family"""
        # Remove second child to test single child pricing
        self.child2.delete()
        
        test_date = date(2025, 1, 8)  # Wednesday
        
        # First 3 sign-ins should be $6.00 each
        for i in range(3):
            current_date = test_date + timedelta(days=i)
            charge, reason = PaymentCalculator.calculate_charge_for_checkin(
                self.child1, current_date
            )
            self.assertEqual(charge, Decimal('6.00'))
            self.assertIn('Standard rate', reason)
            
            # Create attendance record to track the sign-in
            Attendance.objects.create(
                child=self.child1,
                date=current_date,
                time_in=datetime.now(),
                charge_amount=charge,
                charge_reason=reason
            )
        
        # 4th sign-in should be $2.00
        fourth_date = test_date + timedelta(days=3)
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, fourth_date
        )
        self.assertEqual(charge, Decimal('2.00'))
        self.assertIn('Reduced rate', reason)
        
        # Create attendance for 4th sign-in
        Attendance.objects.create(
            child=self.child1,
            date=fourth_date,
            time_in=datetime.now(),
            charge_amount=charge,
            charge_reason=reason
        )
        
        # 5th+ sign-ins should be free
        fifth_date = test_date + timedelta(days=4)
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, fifth_date
        )
        self.assertEqual(charge, Decimal('0.00'))
        self.assertIn('Free', reason)

    def test_multi_child_pricing(self):
        """Test pricing for multi-child family"""
        test_date = date(2025, 1, 8)  # Wednesday
        
        # First 6 sign-ins should be $6.00 each (3 days, both children each day)
        for day_offset in range(3):
            current_date = test_date + timedelta(days=day_offset)
            
            # Sign in child1
            charge, reason = PaymentCalculator.calculate_charge_for_checkin(
                self.child1, current_date
            )
            self.assertEqual(charge, Decimal('6.00'))
            self.assertIn('Standard rate', reason)
            self.assertIn('2 children', reason)
            
            # Create attendance record for child1
            Attendance.objects.create(
                child=self.child1,
                date=current_date,
                time_in=datetime.now(),
                charge_amount=charge,
                charge_reason=reason
            )
            
            # Sign in child2 
            charge, reason = PaymentCalculator.calculate_charge_for_checkin(
                self.child2, current_date
            )
            self.assertEqual(charge, Decimal('6.00'))
            self.assertIn('Standard rate', reason)
            self.assertIn('2 children', reason)
            
            # Create attendance record for child2
            Attendance.objects.create(
                child=self.child2,
                date=current_date,
                time_in=datetime.now(),
                charge_amount=charge,
                charge_reason=reason
            )
        
        # 7th sign-in should be $4.00 (on the 4th day)
        seventh_date = test_date + timedelta(days=3)
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, seventh_date
        )
        self.assertEqual(charge, Decimal('4.00'))
        self.assertIn('Reduced rate', reason)
        
        # Create attendance for 7th sign-in
        Attendance.objects.create(
            child=self.child1,
            date=seventh_date,
            time_in=datetime.now(),
            charge_amount=charge,
            charge_reason=reason
        )
        
        # 8th+ sign-ins should be free (on 5th day)
        eighth_date = test_date + timedelta(days=4)
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child2, eighth_date
        )
        self.assertEqual(charge, Decimal('0.00'))
        self.assertIn('Free', reason)

    def test_daily_family_cap(self):
        """Test daily $12 family cap"""
        test_date = date(2025, 1, 8)
        
        # Create attendance records totaling $10
        Attendance.objects.create(
            child=self.child1,
            date=test_date,
            time_in=datetime.now(),
            charge_amount=Decimal('6.00'),
            charge_reason='Test charge 1'
        )
        Attendance.objects.create(
            child=self.child2,
            date=test_date,
            time_in=datetime.now(),
            charge_amount=Decimal('4.00'),
            charge_reason='Test charge 2'
        )
        
        # Next charge should be capped at $2.00 to reach $12 limit
        # Try to check in a child that hasn't been checked in today
        # Create a third child for this test
        child3 = Child.objects.create(
            parent=self.parent,
            first_name='Child',
            last_name='Three',
            date_of_birth=date(2018, 1, 1),
            gender='boy',
            child_class='K-2'
        )
        
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            child3, test_date
        )
        self.assertEqual(charge, Decimal('2.00'))
        self.assertIn('capped at daily family limit', reason)
        
        # Create attendance for the capped charge
        Attendance.objects.create(
            child=child3,
            date=test_date,
            time_in=datetime.now(),
            charge_amount=Decimal('2.00'),
            charge_reason='Capped charge'
        )
        
        # After cap is reached, any new sign-in should be $0
        child4 = Child.objects.create(
            parent=self.parent,
            first_name='Child',
            last_name='Four',
            date_of_birth=date(2019, 1, 1),
            gender='girl',
            child_class='K-2'
        )
        
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            child4, test_date
        )
        self.assertEqual(charge, Decimal('0.00'))
        self.assertIn('Daily family cap reached', reason)

    def test_no_double_charging_same_day(self):
        """Test that children aren't charged twice on same day"""
        test_date = date(2025, 1, 8)
        
        # Create existing attendance for today
        Attendance.objects.create(
            child=self.child1,
            date=test_date,
            time_in=datetime.now(),
            charge_amount=Decimal('6.00')
        )
        
        # Second check-in same day should be free
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, test_date
        )
        self.assertEqual(charge, Decimal('0.00'))
        self.assertEqual(reason, 'Already checked in today')

    def test_weekly_counter_resets(self):
        """Test that weekly counters reset properly across weeks"""
        # Week 1 - Tuesday Jan 7 to Monday Jan 13
        week1_tuesday = date(2025, 1, 7)
        week1_monday = date(2025, 1, 13)
        
        # Week 2 - Tuesday Jan 14 to Monday Jan 20  
        week2_tuesday = date(2025, 1, 14)
        
        # Fill up week 1 for single child (remove child2)
        self.child2.delete()
        
        # Create 4 sign-ins in week 1 (should exhaust standard + reduced)
        for i in range(4):
            Attendance.objects.create(
                child=self.child1,
                date=week1_tuesday + timedelta(days=i),
                time_in=datetime.now(),
                charge_amount=Decimal('6.00') if i < 3 else Decimal('2.00')
            )
        
        # 5th sign-in in week 1 should be free
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, week1_monday
        )
        self.assertEqual(charge, Decimal('0.00'))
        self.assertIn('Free', reason)
        
        # First sign-in in week 2 should reset to $6.00
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, week2_tuesday
        )
        self.assertEqual(charge, Decimal('6.00'))
        self.assertIn('Standard rate', reason)

    def test_process_checkin_with_payment(self):
        """Test full check-in processing with payment"""
        test_date = date(2025, 1, 8)
        initial_balance = Decimal('50.00')
        
        # Create payment account
        from registration.payment_views import get_or_create_payment_account
        payment_account = get_or_create_payment_account(self.parent)
        payment_account.balance = initial_balance
        payment_account.save()
        
        # Process first check-in
        attendance, charge_amount, charge_reason = PaymentCalculator.process_checkin_with_payment(
            child=self.child1,
            check_date=test_date
        )
        
        # Verify attendance record created
        self.assertIsInstance(attendance, Attendance)
        self.assertEqual(attendance.child, self.child1)
        self.assertEqual(attendance.date, test_date)
        self.assertEqual(attendance.charge_amount, charge_amount)
        self.assertEqual(attendance.charge_reason, charge_reason)
        
        # Verify charge calculation
        self.assertEqual(charge_amount, Decimal('6.00'))
        self.assertIn('Standard rate', charge_reason)
        
        # Verify balance updated
        payment_account.refresh_from_db()
        expected_balance = initial_balance - charge_amount
        self.assertEqual(payment_account.balance, expected_balance)

    def test_insufficient_balance_handling(self):
        """Test behavior when parent has insufficient balance"""
        test_date = date(2025, 1, 8)
        
        # Create payment account with insufficient balance
        from registration.payment_views import get_or_create_payment_account
        payment_account = get_or_create_payment_account(self.parent)
        payment_account.balance = Decimal('3.00')  # Less than $6 required
        payment_account.save()
        
        # Should still calculate correct charge but not process payment
        charge, reason = PaymentCalculator.calculate_charge_for_checkin(
            self.child1, test_date
        )
        self.assertEqual(charge, Decimal('6.00'))
        
        # process_checkin_with_payment should handle this gracefully
        # by creating attendance but not charging (handled by views)

    def test_family_weekly_summary(self):
        """Test weekly summary generation"""
        test_date = date(2025, 1, 8)  # Wednesday
        
        # Create some attendance records
        Attendance.objects.create(
            child=self.child1,
            date=test_date,
            time_in=datetime.now(),
            charge_amount=Decimal('6.00')
        )
        Attendance.objects.create(
            child=self.child2,
            date=test_date + timedelta(days=1),
            time_in=datetime.now(),
            charge_amount=Decimal('6.00')
        )
        
        summary = PaymentCalculator.get_family_weekly_summary(self.parent, test_date)
        
        # Verify summary structure
        self.assertIn('week_start', summary)
        self.assertIn('week_end', summary)
        self.assertIn('family_size', summary)
        self.assertIn('unique_signins', summary)
        self.assertIn('weekly_charges', summary)
        self.assertIn('next_charge_amount', summary)
        self.assertIn('current_balance', summary)
        self.assertIn('threshold', summary)
        
        # Verify calculated values
        self.assertEqual(summary['family_size'], 2)
        self.assertEqual(summary['unique_signins'], 2)
        self.assertEqual(summary['weekly_charges'], Decimal('12.00'))
        self.assertEqual(summary['threshold'], 6)  # Multi-child threshold
        
        # Week should run Tuesday to Monday
        expected_week_start = date(2025, 1, 7)  # Tuesday
        expected_week_end = date(2025, 1, 13)   # Monday
        self.assertEqual(summary['week_start'], expected_week_start)
        self.assertEqual(summary['week_end'], expected_week_end)

    def test_edge_cases(self):
        """Test various edge cases"""
        test_date = date(2025, 1, 8)
        
        # Test with no children
        empty_parent = ParentProfile.objects.create(
            user=User.objects.create_user('empty', 'empty@test.com', 'pass'),
            first_name='Empty',
            last_name='Parent',
            street_address='123 Empty St',
            city='Empty City', 
            postcode='00000',
            email='empty@test.com',
            phone_number='+61400000000',
            how_heard_about='other',
            attends_church_regularly=False,
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+61400000001',
            emergency_contact_relationship='parent',
            first_aid_consent=True,
            injury_waiver=True
        )
        
        summary = PaymentCalculator.get_family_weekly_summary(empty_parent, test_date)
        self.assertEqual(summary['family_size'], 0)
        self.assertEqual(summary['next_charge_amount'], Decimal('0.00'))
        self.assertEqual(summary['next_charge_reason'], 'No children')
        
        # Test boundary conditions for week calculation
        # Monday should belong to previous week
        monday_date = date(2025, 1, 6)
        week_start, week_end = PaymentCalculator.get_week_boundaries(monday_date)
        self.assertEqual(week_start.weekday(), 1)  # Tuesday
        self.assertEqual(week_end.weekday(), 0)    # Monday
