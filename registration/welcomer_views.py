from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Case, When, Value, CharField
from django.db.models.functions import Concat
from .models import ParentProfile, Child, ParentInteraction, WelcomerProfile
from .forms import ParentInteractionForm
from django.contrib.auth.models import User


def is_welcomer_or_staff(user):
    """Check if user is staff or has welcomer profile"""
    return user.is_staff or hasattr(user, 'welcomerprofile')


@login_required
@user_passes_test(is_welcomer_or_staff)
def welcomer_dashboard(request):
    """Main dashboard for welcomers showing recent interactions and summary"""
    
    # Get or create welcomer profile if staff but not welcomer
    welcomer_profile = None
    if hasattr(request.user, 'welcomerprofile'):
        welcomer_profile = request.user.welcomerprofile
    elif request.user.is_staff:
        # Auto-create welcomer profile for staff
        welcomer_profile, created = WelcomerProfile.objects.get_or_create(user=request.user)
    
    # Get recent interactions
    recent_interactions = ParentInteraction.objects.select_related(
        'parent_profile', 'welcomer__user'
    ).order_by('-created_at')[:20]
    
    # Get summary statistics
    total_interactions = ParentInteraction.objects.count()
    unique_people = ParentInteraction.objects.values('parent_profile').distinct().count() + \
                   ParentInteraction.objects.filter(parent_profile__isnull=True)\
                   .values('manual_first_name', 'manual_last_name').distinct().count()
    
    # Daily breakdown
    daily_stats = ParentInteraction.objects.values('interaction_day')\
                    .annotate(count=Count('id'))\
                    .order_by('interaction_day')
    
    # Welcomer stats
    welcomer_stats = ParentInteraction.objects.values('welcomer__user__first_name', 'welcomer__user__last_name')\
                       .annotate(count=Count('id'))\
                       .order_by('-count')[:5]
    
    context = {
        'recent_interactions': recent_interactions,
        'total_interactions': total_interactions,
        'unique_people': unique_people,
        'daily_stats': daily_stats,
        'welcomer_stats': welcomer_stats,
        'welcomer_profile': welcomer_profile,
    }
    
    return render(request, 'registration/welcomer_dashboard.html', context)


@login_required
@user_passes_test(is_welcomer_or_staff)
def add_interaction(request):
    """Add a new parent interaction"""
    
    # Get or create welcomer profile
    welcomer_profile = None
    if hasattr(request.user, 'welcomerprofile'):
        welcomer_profile = request.user.welcomerprofile
    elif request.user.is_staff:
        welcomer_profile, created = WelcomerProfile.objects.get_or_create(user=request.user)
    
    if not welcomer_profile:
        messages.error(request, 'You need welcomer permissions to record interactions.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ParentInteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save(commit=False)
            interaction.welcomer = welcomer_profile
            interaction.save()
            
            person_name = interaction.get_person_name()
            messages.success(request, f'Interaction with {person_name} recorded successfully!')
            return redirect('welcomer_dashboard')
    else:
        form = ParentInteractionForm()
    
    return render(request, 'registration/add_interaction.html', {
        'form': form,
        'welcomer_profile': welcomer_profile
    })


@login_required
@user_passes_test(is_welcomer_or_staff)
def interaction_list(request):
    """List all interactions with filtering and search"""
    
    # Get filter parameters
    day_filter = request.GET.get('day', '')
    welcomer_filter = request.GET.get('welcomer', '')
    search_query = request.GET.get('search', '')
    
    # Start with all interactions
    interactions = ParentInteraction.objects.select_related(
        'parent_profile', 'welcomer__user'
    ).order_by('-created_at')
    
    # Apply filters
    if day_filter:
        interactions = interactions.filter(interaction_day=day_filter)
    
    if welcomer_filter:
        interactions = interactions.filter(welcomer__user__id=welcomer_filter)
    
    if search_query:
        interactions = interactions.filter(
            Q(parent_profile__first_name__icontains=search_query) |
            Q(parent_profile__last_name__icontains=search_query) |
            Q(manual_first_name__icontains=search_query) |
            Q(manual_last_name__icontains=search_query) |
            Q(faith_status__icontains=search_query) |
            Q(knows_lighthouse_members__icontains=search_query)
        )
    
    # Get filter options
    day_choices = ParentInteraction.DAY_CHOICES
    welcomer_choices = [(u.id, u.get_full_name() or u.username) 
                       for u in User.objects.filter(welcomerprofile__isnull=False)]
    
    # Group interactions by person for summary view
    person_summaries = {}
    for interaction in interactions:
        person_key = interaction.parent_profile.id if interaction.parent_profile else f"manual_{interaction.manual_first_name}_{interaction.manual_last_name}"
        
        if person_key not in person_summaries:
            person_summaries[person_key] = {
                'person_name': interaction.get_person_name(),
                'contact_info': interaction.get_contact_info(),
                'children_info': interaction.get_children_info(),
                'interactions': [],
                'faith_status': [],
                'lighthouse_connections': [],
                'welcomers': set(),
            }
        
        person_summaries[person_key]['interactions'].append(interaction)
        if interaction.faith_status:
            person_summaries[person_key]['faith_status'].append(interaction.faith_status)
        if interaction.knows_lighthouse_members:
            person_summaries[person_key]['lighthouse_connections'].append(interaction.knows_lighthouse_members)
        person_summaries[person_key]['welcomers'].add(interaction.welcomer.user.get_full_name() or interaction.welcomer.user.username)
    
    context = {
        'interactions': interactions,
        'person_summaries': person_summaries,
        'day_filter': day_filter,
        'welcomer_filter': welcomer_filter,
        'search_query': search_query,
        'day_choices': day_choices,
        'welcomer_choices': welcomer_choices,
    }
    
    return render(request, 'registration/interaction_list.html', context)


@login_required
@user_passes_test(is_welcomer_or_staff)
def interaction_detail(request, interaction_id):
    """View details of a specific interaction"""
    
    interaction = get_object_or_404(ParentInteraction, id=interaction_id)
    
    # Get all interactions for this person
    if interaction.parent_profile:
        all_interactions = ParentInteraction.get_all_interactions_for_person(
            parent_profile=interaction.parent_profile
        )
    else:
        person_name = f"{interaction.manual_first_name} {interaction.manual_last_name}"
        all_interactions = ParentInteraction.get_all_interactions_for_person(
            manual_name=person_name
        )
    
    context = {
        'interaction': interaction,
        'all_interactions': all_interactions,
        'person_name': interaction.get_person_name(),
        'contact_info': interaction.get_contact_info(),
        'children_info': interaction.get_children_info(),
    }
    
    return render(request, 'registration/interaction_detail.html', context)


@login_required
@user_passes_test(is_welcomer_or_staff)
def edit_interaction(request, interaction_id):
    """Edit an existing interaction"""
    
    interaction = get_object_or_404(ParentInteraction, id=interaction_id)
    
    # Only allow editing by the original welcomer or staff
    if not request.user.is_staff and interaction.welcomer.user != request.user:
        messages.error(request, 'You can only edit your own interactions.')
        return redirect('interaction_detail', interaction_id=interaction.id)
    
    if request.method == 'POST':
        form = ParentInteractionForm(request.POST, instance=interaction)
        if form.is_valid():
            form.save()
            person_name = interaction.get_person_name()
            messages.success(request, f'Interaction with {person_name} updated successfully!')
            return redirect('interaction_detail', interaction_id=interaction.id)
    else:
        form = ParentInteractionForm(instance=interaction)
    
    return render(request, 'registration/edit_interaction.html', {
        'form': form,
        'interaction': interaction
    })


@login_required
@user_passes_test(is_welcomer_or_staff)
def get_parent_info(request):
    """AJAX endpoint to get parent information"""
    
    parent_id = request.GET.get('parent_id')
    if not parent_id:
        return JsonResponse({'error': 'No parent ID provided'})
    
    try:
        parent = ParentProfile.objects.get(id=parent_id)
        children = parent.children.all()
        
        children_data = []
        for child in children:
            children_data.append({
                'name': f"{child.first_name} {child.last_name}",
                'class': child.get_class_short_name(),
                'age_class': child.get_child_class_display()
            })
        
        data = {
            'name': f"{parent.first_name} {parent.last_name}",
            'phone': parent.phone_number,
            'email': parent.email,
            'address': f"{parent.street_address}, {parent.city} {parent.postcode}",
            'children': children_data
        }
        
        return JsonResponse(data)
        
    except ParentProfile.DoesNotExist:
        return JsonResponse({'error': 'Parent not found'})


@login_required
@user_passes_test(is_welcomer_or_staff)
def get_child_parent_info(request):
    """AJAX endpoint to get parent information from child selection"""
    
    child_id = request.GET.get('child_id')
    if not child_id:
        return JsonResponse({'error': 'No child ID provided'})
    
    try:
        child = Child.objects.select_related('parent').get(id=child_id)
        parent = child.parent
        
        # Get all children for this parent
        children = parent.children.all()
        children_data = []
        for sibling in children:
            children_data.append({
                'name': f"{sibling.first_name} {sibling.last_name}",
                'class': sibling.get_class_short_name(),
                'age_class': sibling.get_child_class_display()
            })
        
        data = {
            'parent_id': parent.id,
            'name': f"{parent.first_name} {parent.last_name}",
            'phone': parent.phone_number,
            'email': parent.email,
            'address': f"{parent.street_address}, {parent.city} {parent.postcode}",
            'children': children_data,
            'selected_child': f"{child.first_name} {child.last_name}"
        }
        
        return JsonResponse(data)
        
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'})
