"""
Payment views for Summerfest registration system
Handles Stripe payments, manual payments, and payment tracking
"""

import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import ParentProfile, PaymentAccount, PaymentTransaction, DailyAttendanceCharge
from .forms import AddFundsForm, ManualPaymentForm

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_payment_account(parent_profile):
    """Get or create payment account for parent"""
    account, created = PaymentAccount.objects.get_or_create(
        parent_profile=parent_profile,
        defaults={'balance': Decimal('0.00')}
    )
    return account


@login_required
def payment_dashboard(request):
    """Payment dashboard for parents"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    # Get or create payment account
    payment_account = get_or_create_payment_account(parent_profile)
    
    # Get recent transactions
    recent_transactions = payment_account.transactions.all()[:10]
    
    # Get daily charges
    daily_charges = payment_account.daily_charges.all()[:10]
    
    # Calculate estimated daily cost for this family
    children = parent_profile.children.all()
    # Estimate cost based on new system: $6 for early sign-ins
    estimated_daily_cost = Decimal('6.00') if children else Decimal('0.00')
    
    context = {
        'payment_account': payment_account,
        'recent_transactions': recent_transactions,
        'daily_charges': daily_charges,
        'estimated_daily_cost': estimated_daily_cost,
        'children': children,
    }
    
    return render(request, 'registration/payment_dashboard.html', context)


@login_required
def add_funds(request):
    """Add funds to payment account"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    payment_account = get_or_create_payment_account(parent_profile)
    
    if request.method == 'POST':
        form = AddFundsForm(request.POST)
        if form.is_valid():
            amount = form.get_amount()
            
            # Create Stripe checkout session
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    payment_method_options={
                        'card': {
                            'request_three_d_secure': 'automatic',
                        }
                    },
                    line_items=[{
                        'price_data': {
                            'currency': settings.PAYMENT_CURRENCY.lower(),
                            'product_data': {
                                'name': 'Summerfest Account Credit',
                                'description': f'Add ${amount} to your Summerfest account',
                            },
                            'unit_amount': int(amount * 100),  # Stripe uses cents
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
                    metadata={
                        'parent_profile_id': parent_profile.id,
                        'amount': str(amount),
                        'payment_type': 'add_funds'
                    }
                )
                return redirect(checkout_session.url)
            except stripe.error.StripeError as e:
                messages.error(request, f'Payment error: {str(e)}')
    else:
        form = AddFundsForm()
    
    return render(request, 'registration/add_funds.html', {
        'form': form,
        'payment_account': payment_account,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY
    })


@login_required
def payment_success(request):
    """Handle successful payment"""
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('payment_dashboard')
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get parent profile from metadata
            parent_profile_id = session.metadata.get('parent_profile_id')
            amount = Decimal(session.metadata.get('amount'))
            
            parent_profile = get_object_or_404(ParentProfile, id=parent_profile_id)
            payment_account = get_or_create_payment_account(parent_profile)
            
            # Check if we've already processed this payment
            existing_transaction = PaymentTransaction.objects.filter(
                stripe_payment_intent_id=session.payment_intent
            ).first()
            
            if not existing_transaction:
                # Add funds to account
                payment_account.add_funds(
                    amount,
                    f"Online card payment - ${amount}"
                )
                
                # Update transaction with Stripe details
                transaction = payment_account.transactions.filter(
                    amount=amount,
                    description=f"Online card payment - ${amount}"
                ).first()
                
                if transaction:
                    transaction.stripe_payment_intent_id = session.payment_intent
                    transaction.payment_method = 'stripe'
                    transaction.save()
                
                messages.success(request, f'Payment successful! ${amount} has been added to your account.')
            else:
                messages.info(request, 'This payment has already been processed.')
        else:
            messages.error(request, 'Payment was not completed successfully.')
            
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment verification error: {str(e)}')
    
    return redirect('payment_dashboard')


@login_required 
def payment_cancel(request):
    """Handle cancelled payment"""
    messages.warning(request, 'Payment was cancelled.')
    return redirect('payment_dashboard')


@login_required
@user_passes_test(lambda user: user.is_staff or hasattr(user, 'teacherprofile'))
def manual_payment(request):
    """Record manual payments (cash/eftpos) by staff"""
    if request.method == 'POST':
        form = ManualPaymentForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['parent_username']
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            notes = form.cleaned_data['notes']
            
            # Get parent and payment account
            user = User.objects.get(username=username)
            parent_profile = user.parentprofile
            payment_account = get_or_create_payment_account(parent_profile)
            
            # Add funds
            description = f"{payment_method.upper()} payment"
            if notes:
                description += f" - {notes}"
            
            payment_account.add_funds(amount, description)
            
            # Update transaction with staff details
            transaction = payment_account.transactions.first()
            transaction.payment_method = payment_method
            transaction.recorded_by = request.user
            transaction.save()
            
            messages.success(request, f'${amount} {payment_method} payment recorded for {parent_profile.first_name} {parent_profile.last_name}')
            
            # Clear form for next entry
            form = ManualPaymentForm()
    else:
        form = ManualPaymentForm()
    
    return render(request, 'registration/manual_payment.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.is_staff or hasattr(user, 'teacherprofile'))
def payment_lookup(request):
    """Quick payment account lookup for staff"""
    parent_profile = None
    payment_account = None
    
    username = request.GET.get('username')
    if username:
        try:
            user = User.objects.get(username=username)
            if hasattr(user, 'parentprofile'):
                parent_profile = user.parentprofile
                payment_account = get_or_create_payment_account(parent_profile)
        except User.DoesNotExist:
            messages.error(request, f'User "{username}" not found.')
    
    return render(request, 'registration/payment_lookup.html', {
        'parent_profile': parent_profile,
        'payment_account': payment_account,
        'search_username': username
    })


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Payment success is already handled in payment_success view
        pass
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Update transaction if needed
        pass
    
    return HttpResponse(status=200)
