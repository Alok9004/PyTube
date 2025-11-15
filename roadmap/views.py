from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from .models import Roadmap, Milestone, RoadmapVideo, UserRoadmapProgress, UserMilestoneProgress
from channels.models import Channel
from videos.models import Video
from .forms import RoadmapForm, MilestoneForm
import json

def roadmap_list(request):
    # Show published roadmaps to all users, drafts to owners
    if request.user.is_authenticated:
        roadmaps = Roadmap.objects.filter(
            Q(status='published') | 
            Q(created_by=request.user)
        ).select_related('channel', 'created_by').distinct()
    else:
        roadmaps = Roadmap.objects.filter(status='published').select_related('channel', 'created_by')
    
    # Filters
    level = request.GET.get('level')
    channel_id = request.GET.get('channel')
    search = request.GET.get('search')
    
    if level:
        roadmaps = roadmaps.filter(level=level)
    if channel_id:
        roadmaps = roadmaps.filter(channel_id=channel_id)
    if search:
        roadmaps = roadmaps.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Prepare roadmap data with progress
    roadmap_data = []
    for roadmap in roadmaps:
        roadmap_info = {
            'roadmap': roadmap,
            'user_progress': None,
            'is_owner': request.user == roadmap.created_by
        }
        
        if request.user.is_authenticated:
            try:
                progress = UserRoadmapProgress.objects.get(
                    user=request.user,
                    roadmap=roadmap
                )
                roadmap_info['user_progress'] = progress
            except UserRoadmapProgress.DoesNotExist:
                pass
                
        roadmap_data.append(roadmap_info)
    
    channels = Channel.objects.all()
    
    context = {
        'roadmap_data': roadmap_data,
        'channels': channels,
        'current_filters': {
            'level': level,
            'channel': channel_id,
            'search': search,
        }
    }
    
    return render(request, 'roadmap/list.html', context)

def roadmap_detail(request, roadmap_id):
    # Get roadmap without status filter first
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    # Check if user can view this roadmap
    can_view = (
        roadmap.status == 'published' or 
        (request.user.is_authenticated and request.user == roadmap.created_by)
    )
    
    if not can_view:
        messages.error(request, "This roadmap is not available or you don't have permission to view it.")
        return redirect('roadmap:roadmap_list')
    
    milestones = roadmap.milestones.all().prefetch_related('roadmap_videos__video')
    
    user_progress = None
    milestone_progress = {}
    
    if request.user.is_authenticated:
        user_progress = UserRoadmapProgress.objects.filter(
            user=request.user, roadmap=roadmap
        ).first()
        
        if user_progress:
            milestone_progress_obj = UserMilestoneProgress.objects.filter(
                user=request.user,
                milestone__in=milestones
            )
            for progress in milestone_progress_obj:
                milestone_progress[progress.milestone_id] = progress
    
    # Related roadmaps (only published ones)
    related_roadmaps = Roadmap.objects.filter(
        channel=roadmap.channel,
        status='published'
    ).exclude(id=roadmap.id)[:4]
    
    context = {
        'roadmap': roadmap,
        'milestones': milestones,
        'user_progress': user_progress,
        'milestone_progress': milestone_progress,
        'related_roadmaps': related_roadmaps,
        'can_edit': request.user == roadmap.created_by,
    }
    
    return render(request, 'roadmap/detail.html', context)

@login_required
def start_roadmap(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    # Check if roadmap is published or user is owner
    if roadmap.status != 'published' and request.user != roadmap.created_by:
        messages.error(request, "This roadmap is not available for starting.")
        return redirect('roadmap:roadmap_list')
    
    # Check if user already started this roadmap
    user_progress, created = UserRoadmapProgress.objects.get_or_create(
        user=request.user,
        roadmap=roadmap,
        defaults={'current_milestone': roadmap.milestones.first()}
    )
    
    if created:
        # Initialize progress for all milestones
        for milestone in roadmap.milestones.all():
            UserMilestoneProgress.objects.get_or_create(
                user=request.user,
                milestone=milestone
            )
        messages.success(request, f'You have started the "{roadmap.title}" roadmap!')
    else:
        messages.info(request, f'You are already following the "{roadmap.title}" roadmap')
    
    return redirect('roadmap:roadmap_detail', roadmap_id=roadmap_id)

@login_required
def roadmap_progress(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    user_progress = get_object_or_404(UserRoadmapProgress, user=request.user, roadmap=roadmap)
    milestones = roadmap.milestones.all()
    
    milestone_progress = UserMilestoneProgress.objects.filter(
        user=request.user,
        milestone__in=milestones
    ).select_related('milestone')
    
    # Calculate overall progress
    total_milestones = milestones.count()
    completed_milestones = milestone_progress.filter(is_completed=True).count()
    
    overall_progress = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
    
    context = {
        'roadmap': roadmap,
        'user_progress': user_progress,
        'milestone_progress': milestone_progress,
        'overall_progress': overall_progress,
        'completed_milestones': completed_milestones,
        'total_milestones': total_milestones,
    }
    
    return render(request, 'roadmap/progress.html', context)

@login_required
def my_roadmaps(request):
    user_roadmaps = UserRoadmapProgress.objects.filter(
        user=request.user
    ).select_related('roadmap', 'roadmap__channel')
    
    in_progress = user_roadmaps.filter(is_completed=False)
    completed = user_roadmaps.filter(is_completed=True)
    
    context = {
        'in_progress_roadmaps': in_progress,
        'completed_roadmaps': completed,
    }
    
    return render(request, 'roadmap/my_roadmaps.html', context)

@login_required
def complete_milestone(request, milestone_id):
    if request.method == 'POST':
        milestone = get_object_or_404(Milestone, id=milestone_id)
        user_progress, created = UserMilestoneProgress.objects.get_or_create(
            user=request.user,
            milestone=milestone
        )
        
        user_progress.is_completed = True
        user_progress.completed_at = timezone.now()
        user_progress.completed_videos = milestone.videos_count
        user_progress.save()
        
        # Check if roadmap is completed
        roadmap_progress = UserRoadmapProgress.objects.get(
            user=request.user,
            roadmap=milestone.roadmap
        )
        
        all_milestones_completed = not UserMilestoneProgress.objects.filter(
            user=request.user,
            milestone__roadmap=milestone.roadmap,
            is_completed=False
        ).exists()
        
        if all_milestones_completed:
            roadmap_progress.is_completed = True
            roadmap_progress.completed_at = timezone.now()
            roadmap_progress.save()
            messages.success(request, f'Congratulations! You completed the "{milestone.roadmap.title}" roadmap!')
        else:
            messages.success(request, f'Milestone "{milestone.title}" completed!')
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def roadmap_create(request):
    if request.method == 'POST':
        form = RoadmapForm(request.POST)
        if form.is_valid():
            roadmap = form.save(commit=False)
            roadmap.created_by = request.user
            roadmap.status = 'published'  # Auto-publish when created
            roadmap.save()
            messages.success(request, 'Roadmap created successfully!')
            return redirect('roadmap:roadmap_detail', roadmap_id=roadmap.id)
    else:
        form = RoadmapForm()
    
    channels = Channel.objects.all()
    return render(request, 'roadmap/form.html', {'form': form, 'channels': channels})

@login_required
def roadmap_edit(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, created_by=request.user)
    
    if request.method == 'POST':
        form = RoadmapForm(request.POST, instance=roadmap)
        if form.is_valid():
            form.save()
            messages.success(request, 'Roadmap updated successfully!')
            return redirect('roadmap:roadmap_detail', roadmap_id=roadmap.id)
    else:
        form = RoadmapForm(instance=roadmap)
    
    return render(request, 'roadmap/form.html', {'form': form, 'editing': True})

@login_required
def roadmap_delete(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, created_by=request.user)
    
    if request.method == 'POST':
        roadmap.delete()
        messages.success(request, 'Roadmap deleted successfully!')
        return redirect('roadmap:roadmap_list')
    
    return render(request, 'roadmap/confirm_delete.html', {'roadmap': roadmap})

def roadmap_search(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        roadmaps = Roadmap.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query),
            status='published'
        )[:10]
        
        for roadmap in roadmaps:
            results.append({
                'id': roadmap.id,
                'title': roadmap.title,
                'description': roadmap.description[:100] + '...' if len(roadmap.description) > 100 else roadmap.description,
                'channel': roadmap.channel.name,
                'level': roadmap.get_level_display(),
                'thumbnail': roadmap.thumbnail,
            })
    
    return JsonResponse({'results': results})