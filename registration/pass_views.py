"""
Views for the pass purchase system
"""
import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from decimal import Decimal
from datetime import date
from .models import ParentProfile, Pass
from .pass_forms import PurchasePassForm

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def purchase_pass(request):
    """Purchase a pass for Summerfest attendance"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    if request.method == 'POST':
        form = PurchasePassForm(request.POST)
        if form.is_valid():
            pass_type = form.cleaned_data['pass_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.get_end_date()
            price = form.get_price()
            
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
                                'name': f'Summerfest {dict(form.PASS_CHOICES)[pass_type]}',
                                'description': f'Valid from {start_date} to {end_date}',
                            },
                            'unit_amount': int(price * 100),  # Stripe uses cents
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri(reverse('pass_purchase_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri(reverse('pass_purchase_cancel')),
                    metadata={
                        'parent_profile_id': parent_profile.id,
                        'pass_type': pass_type,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'amount': str(price),
                        'payment_type': 'pass_purchase'
                    }
                )
                return redirect(checkout_session.url)
            except stripe.error.StripeError as e:
                messages.error(request, f'Payment error: {str(e)}')
    else:
        form = PurchasePassForm()
    
    # Get existing passes
    existing_passes = Pass.objects.filter(parent=parent_profile).order_by('-created_at')
    
    # Get children count for recommendations
    children_count = parent_profile.children.count()
    
    context = {
        'form': form,
        'existing_passes': existing_passes,
        'children_count': children_count,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY
    }
    
    return render(request, 'registration/purchase_pass.html', context)


@login_required
def pass_purchase_success(request):
    """Handle successful pass purchase"""
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('purchase_pass')
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get metadata from session
            parent_profile_id = session.metadata.get('parent_profile_id')
            pass_type = session.metadata.get('pass_type')
            start_date = session.metadata.get('start_date')
            end_date = session.metadata.get('end_date')
            amount = Decimal(session.metadata.get('amount'))
            
            parent_profile = get_object_or_404(ParentProfile, id=parent_profile_id)
            
            # Check if we've already processed this payment
            existing_pass = Pass.objects.filter(
                stripe_session_id=session_id
            ).first()
            
            if not existing_pass:
                # Create the pass
                pass_obj = Pass.objects.create(
                    type=pass_type,
                    parent=parent_profile,
                    valid_from=start_date,
                    valid_to=end_date,
                    amount_paid=amount,
                    stripe_payment_id=session.payment_intent,
                    stripe_session_id=session_id
                )
                
                pass_display = dict(PurchasePassForm.PASS_CHOICES)[pass_type]
                messages.success(request, f'Pass purchased successfully! {pass_display} is now active from {start_date} to {end_date}.')
            else:
                messages.info(request, 'This pass has already been processed.')
        else:
            messages.error(request, 'Payment was not completed successfully.')
            
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment verification error: {str(e)}')
    
    return redirect('purchase_pass')


@login_required 
def pass_purchase_cancel(request):
    """Handle cancelled pass purchase"""
    messages.warning(request, 'Pass purchase was cancelled.')
    return redirect('purchase_pass')


@login_required
def my_passes(request):
    """Display user's current passes"""
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Please complete your registration first.')
        return redirect('parent_register')
    
    passes = Pass.objects.filter(parent=parent_profile).order_by('-created_at')
    
    # Categorize passes
    valid_passes = []
    expired_passes = []
    
    today = date.today()
    for pass_obj in passes:
        if pass_obj.is_valid_for_date(today):
            valid_passes.append(pass_obj)
        else:
            expired_passes.append(pass_obj)
    
    context = {
        'valid_passes': valid_passes,
        'expired_passes': expired_passes,
        'today': today
    }
    
    return render(request, 'registration/my_passes.html', context)
