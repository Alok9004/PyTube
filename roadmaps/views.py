from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import models
from django.utils import timezone
from django.db.models import Count, Q, Sum, Prefetch

from .models import Roadmap, RoadmapChannel, RoadmapFollow
from channels.models import Channel
from videos.models import Video, VideoProgress
from .forms import RoadmapForm, RoadmapChannelForm


def calculate_roadmap_progress(roadmap, user):
    """Calculate comprehensive progress data for roadmap"""
    channels_with_progress = []
    total_completed_videos = 0
    total_videos = 0
    total_watched_seconds = 0
    
    # Get user's video progress for all videos in roadmap
    user_video_progress = {}
    if user.is_authenticated:
        video_ids = [video.id for channel in roadmap.channels.all() for video in channel.channel.videos.all()]
        progress_objects = VideoProgress.objects.filter(
            user=user, 
            video_id__in=video_ids
        ).values('video_id', 'current_time', 'watched_percentage')
        
        for progress in progress_objects:
            user_video_progress[progress['video_id']] = progress
    
    for roadmap_channel in roadmap.channels.all():
        channel = roadmap_channel.channel
        videos = channel.videos.all()
        channel_total_videos = videos.count()
        total_videos += channel_total_videos
        
        # Calculate channel progress
        completed_videos = 0
        channel_watched_seconds = 0
        
        for video in videos:
            progress = user_video_progress.get(video.id)
            if progress and progress['watched_percentage'] >= 95:
                completed_videos += 1
            if progress:
                channel_watched_seconds += progress['current_time']
        
        total_completed_videos += completed_videos
        total_watched_seconds += channel_watched_seconds
        
        channel_progress = int((completed_videos / channel_total_videos) * 100) if channel_total_videos > 0 else 0
        
        channels_with_progress.append({
            'roadmap_channel': roadmap_channel,
            'progress': channel_progress,
            'completed_videos': completed_videos,
            'total_videos': channel_total_videos,
            'watched_seconds': channel_watched_seconds,
        })
    
    # Calculate overall progress
    overall_progress = int((total_completed_videos / total_videos) * 100) if total_videos > 0 else 0
    total_watched_hours = total_watched_seconds / 3600
    
    return {
        'channels_with_progress': channels_with_progress,
        'overall_progress': overall_progress,
        'total_completed_videos': total_completed_videos,
        'total_videos': total_videos,
        'total_watched_hours': round(total_watched_hours, 1),
    }


class RoadmapListView(ListView):
    model = Roadmap
    template_name = 'roadmaps/list.html'
    context_object_name = 'roadmaps'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Roadmap.objects.filter(is_public=True).select_related('owner')
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(owner__username__icontains=search_query)
            )
        
        # Filters
        difficulty = self.request.GET.get('difficulty')
        if difficulty in ['beginner', 'intermediate', 'advanced']:
            queryset = queryset.filter(difficulty=difficulty)
        
        max_hours = self.request.GET.get('max_hours')
        if max_hours and max_hours.isdigit():
            queryset = queryset.filter(estimated_hours__lte=int(max_hours))
        
        # Ordering
        order_by = self.request.GET.get('order_by', '-created_at')
        ordering_map = {
            'title': 'title',
            '-title': '-title',
            'followers': '-follower_count',
            'difficulty': 'difficulty',
            'estimated_hours': 'estimated_hours'
        }
        
        if order_by in ordering_map:
            if order_by == 'followers':
                queryset = queryset.annotate(follower_count=Count('followers'))
            queryset = queryset.order_by(ordering_map[order_by])
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'selected_difficulty': self.request.GET.get('difficulty', ''),
            'selected_max_hours': self.request.GET.get('max_hours', ''),
            'order_by': self.request.GET.get('order_by', '-created_at'),
        })
        return context


class RoadmapDetailView(DetailView):
    model = Roadmap
    template_name = 'roadmaps/detail.html'
    context_object_name = 'roadmap'
    
    def get_queryset(self):
        return Roadmap.objects.select_related('owner').prefetch_related(
            Prefetch('channels', queryset=RoadmapChannel.objects.select_related('channel').order_by('order')),
            'channels__channel__videos'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roadmap = self.object
        
        # Get user follow status
        user_follow = None
        is_following = False
        if self.request.user.is_authenticated:
            try:
                user_follow = RoadmapFollow.objects.get(user=self.request.user, roadmap=roadmap)
                is_following = True
            except RoadmapFollow.DoesNotExist:
                pass
        
        # Calculate progress
        progress_data = calculate_roadmap_progress(roadmap, self.request.user)
        
        context.update({
            'is_following': is_following,
            'user_follow': user_follow,
            'can_edit': self.request.user == roadmap.owner,
            **progress_data
        })
        return context


class RoadmapCreateView(LoginRequiredMixin, CreateView):
    model = Roadmap
    form_class = RoadmapForm
    template_name = 'roadmaps/form.html'
    success_url = reverse_lazy('roadmaps:my_roadmaps')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Roadmap "{self.object.title}" created successfully!')
        return response


class RoadmapUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Roadmap
    form_class = RoadmapForm
    template_name = 'roadmaps/form.html'
    
    def test_func(self):
        return self.request.user == self.get_object().owner
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Roadmap "{self.object.title}" updated successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('roadmaps:detail', kwargs={'pk': self.object.pk})


class RoadmapDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Roadmap
    template_name = 'roadmaps/confirm_delete.html'
    success_url = reverse_lazy('roadmaps:my_roadmaps')
    
    def test_func(self):
        return self.request.user == self.get_object().owner
    
    def delete(self, request, *args, **kwargs):
        roadmap = self.get_object()
        messages.success(request, f'Roadmap "{roadmap.title}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def add_channel_to_roadmap(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, owner=request.user)
    
    if request.method == 'POST':
        form = RoadmapChannelForm(request.POST)
        if form.is_valid():
            roadmap_channel = form.save(commit=False)
            roadmap_channel.roadmap = roadmap
            
            # Check for duplicate order
            if RoadmapChannel.objects.filter(roadmap=roadmap, order=roadmap_channel.order).exists():
                messages.error(request, 'A channel with this order already exists.')
            else:
                roadmap_channel.save()
                messages.success(request, f'Channel "{roadmap_channel.channel.name}" added successfully!')
                return redirect('roadmaps:detail', pk=roadmap_id)
    else:
        form = RoadmapChannelForm()
        # Set available channels and suggest next order
        existing_channel_ids = roadmap.channels.values_list('channel_id', flat=True)
        form.fields['channel'].queryset = Channel.objects.exclude(id__in=existing_channel_ids)
        max_order = roadmap.channels.aggregate(models.Max('order'))['order__max'] or 0
        form.fields['order'].initial = max_order + 1
    
    return render(request, 'roadmaps/add_channel.html', {
        'form': form,
        'roadmap': roadmap
    })


@login_required
def remove_channel_from_roadmap(request, roadmap_id, channel_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, owner=request.user)
    roadmap_channel = get_object_or_404(RoadmapChannel, roadmap=roadmap, channel_id=channel_id)
    
    if request.method == 'POST':
        channel_name = roadmap_channel.channel.name
        roadmap_channel.delete()
        messages.success(request, f'Channel "{channel_name}" removed successfully!')
        return redirect('roadmaps:detail', pk=roadmap_id)
    
    return render(request, 'roadmaps/remove_channel.html', {
        'roadmap': roadmap,
        'roadmap_channel': roadmap_channel
    })


@login_required
def follow_roadmap(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, is_public=True)
    
    if request.method == 'POST':
        follow, created = RoadmapFollow.objects.get_or_create(
            user=request.user, 
            roadmap=roadmap
        )
        if created:
            messages.success(request, f'You are now following "{roadmap.title}"!')
        else:
            messages.info(request, f'You are already following "{roadmap.title}"')
        
        return redirect('roadmaps:detail', pk=roadmap_id)
    
    return render(request, 'roadmaps/follow.html', {'roadmap': roadmap})


@login_required
def unfollow_roadmap(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    if request.method == 'POST':
        deleted_count, _ = RoadmapFollow.objects.filter(user=request.user, roadmap=roadmap).delete()
        if deleted_count:
            messages.success(request, f'You have unfollowed "{roadmap.title}"')
        else:
            messages.error(request, 'You are not following this roadmap')
        
        return redirect('roadmaps:my_roadmaps')
    
    return render(request, 'roadmaps/unfollow.html', {'roadmap': roadmap})


@login_required
def my_roadmaps(request):
    """User's dashboard for created and followed roadmaps"""
    created_roadmaps = Roadmap.objects.filter(owner=request.user).annotate(
        channel_count=Count('channels'),
        follower_count=Count('followers')
    ).order_by('-created_at')
    
    roadmap_follows = RoadmapFollow.objects.filter(user=request.user).select_related('roadmap')
    
    # Calculate progress for followed roadmaps
    followed_with_progress = []
    for follow in roadmap_follows:
        progress_data = calculate_roadmap_progress(follow.roadmap, request.user)
        followed_with_progress.append({
            'follow': follow,
            'progress_data': progress_data
        })
    
    # Calculate total watched time
    total_watched = VideoProgress.objects.filter(user=request.user).aggregate(
        total=Sum('current_time')
    )['total'] or 0
    total_watched_hours = round(total_watched / 3600, 1)
    
    stats = {
        'created_count': created_roadmaps.count(),
        'following_count': roadmap_follows.count(),
        'completed_count': roadmap_follows.filter(completed_at__isnull=False).count(),
        'total_watched_hours': total_watched_hours,
    }
    
    return render(request, 'roadmaps/my_roadmaps.html', {
        'created_roadmaps': created_roadmaps,
        'followed_with_progress': followed_with_progress,
        'stats': stats,
    })


@login_required
def update_roadmap_progress(request, roadmap_id):
    """Update channel progress in roadmap"""
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    if request.method == 'POST':
        try:
            follow = RoadmapFollow.objects.get(user=request.user, roadmap=roadmap)
            action = request.POST.get('action')
            
            if action == 'next':
                follow.current_channel_order = min(follow.current_channel_order + 1, roadmap.channels.count())
            elif action == 'prev':
                follow.current_channel_order = max(follow.current_channel_order - 1, 0)
            elif action == 'set':
                channel_order = int(request.POST.get('channel_order', 0))
                follow.current_channel_order = min(channel_order, roadmap.channels.count())
            
            # Check completion
            if follow.current_channel_order >= roadmap.channels.count():
                follow.completed_at = timezone.now()
                messages.success(request, f'🎉 Congratulations! You completed "{roadmap.title}"!')
            else:
                follow.completed_at = None
            
            follow.save()
            messages.success(request, 'Progress updated successfully!')
            
        except RoadmapFollow.DoesNotExist:
            messages.error(request, 'You are not following this roadmap')
        
        return redirect('roadmaps:detail', pk=roadmap_id)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def auto_update_progress(request, roadmap_id):
    """Automatically update progress based on video completion"""
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    try:
        follow = RoadmapFollow.objects.get(user=request.user, roadmap=roadmap)
        progress_data = calculate_roadmap_progress(roadmap, request.user)
        
        # Find the highest completed channel based on video progress
        highest_completed_order = 0
        for channel_data in progress_data['channels_with_progress']:
            if channel_data['progress'] == 100:  # Channel fully completed
                highest_completed_order = channel_data['roadmap_channel'].order
            else:
                break  # Stop at first incomplete channel
        
        if highest_completed_order > follow.current_channel_order:
            follow.current_channel_order = highest_completed_order
            
            # Check if roadmap is completed
            if follow.current_channel_order >= roadmap.channels.count():
                follow.completed_at = timezone.now()
                messages.success(request, f'🎉 Congratulations! You completed "{roadmap.title}"!')
            else:
                follow.completed_at = None
            
            follow.save()
            messages.success(request, 'Progress auto-updated based on video completion!')
        else:
            messages.info(request, 'No new progress to update based on your video completion.')
            
    except RoadmapFollow.DoesNotExist:
        messages.error(request, 'You are not following this roadmap')
    
    return redirect('roadmaps:detail', pk=roadmap_id)


@login_required
def roadmap_recommendations(request):
    """Get personalized roadmap recommendations"""
    # Get excluded roadmaps (already followed or created)
    excluded_ids = list(
        RoadmapFollow.objects.filter(user=request.user).values_list('roadmap_id', flat=True)
    ) + list(
        Roadmap.objects.filter(owner=request.user).values_list('id', flat=True)
    )
    
    # Get user's preferred difficulty
    user_difficulty = Roadmap.objects.filter(
        roadmapfollow__user=request.user
    ).values('difficulty').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    preferred_difficulty = user_difficulty['difficulty'] if user_difficulty else 'beginner'
    
    # Get recommendations
    recommendations = Roadmap.objects.filter(
        is_public=True
    ).exclude(
        id__in=excluded_ids
    ).annotate(
        follower_count=Count('followers')
    ).order_by('-follower_count')[:8]
    
    # Fallback to difficulty-based if not enough
    if recommendations.count() < 4:
        additional = Roadmap.objects.filter(
            is_public=True,
            difficulty=preferred_difficulty
        ).exclude(id__in=excluded_ids)[:4]
        recommendations = list(recommendations) + list(additional)
    
    return render(request, 'roadmaps/recommendations.html', {
        'recommendations': recommendations,
        'preferred_difficulty': preferred_difficulty,
    })


@login_required
def roadmap_stats(request):
    """User learning statistics"""
    created_count = Roadmap.objects.filter(owner=request.user).count()
    following_count = RoadmapFollow.objects.filter(user=request.user).count()
    completed_count = RoadmapFollow.objects.filter(user=request.user, completed_at__isnull=False).count()
    
    # Calculate total watched time
    total_watched = VideoProgress.objects.filter(user=request.user).aggregate(
        total=Sum('current_time')
    )['total'] or 0
    total_watched_hours = round(total_watched / 3600, 1)
    
    stats = {
        'created_count': created_count,
        'following_count': following_count,
        'completed_count': completed_count,
        'total_watched_hours': total_watched_hours,
        'completion_rate': int((completed_count / following_count) * 100) if following_count > 0 else 0,
    }
    
    return render(request, 'roadmaps/stats.html', {'stats': stats})


def roadmap_categories(request):
    """Browse roadmaps by difficulty categories"""
    categories = {}
    for difficulty, display_name in Roadmap.DIFFICULTY_CHOICES:
        categories[difficulty] = {
            'roadmaps': Roadmap.objects.filter(
                is_public=True, difficulty=difficulty
            ).annotate(
                follower_count=Count('followers')
            ).order_by('-follower_count')[:6],
            'display_name': display_name,
            'icon': {'beginner': '🎯', 'intermediate': '🚀', 'advanced': '🏆'}[difficulty]
        }
    
    return render(request, 'roadmaps/categories.html', {'categories': categories})


@login_required
def reset_progress(request, roadmap_id):
    """Reset progress for a roadmap"""
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    
    if request.method == 'POST':
        try:
            follow = RoadmapFollow.objects.get(user=request.user, roadmap=roadmap)
            follow.current_channel_order = 0
            follow.completed_at = None
            follow.save()
            messages.success(request, f'Progress reset for "{roadmap.title}"')
        except RoadmapFollow.DoesNotExist:
            messages.error(request, 'You are not following this roadmap')
        
        return redirect('roadmaps:detail', pk=roadmap_id)
    
    return render(request, 'roadmaps/reset_progress.html', {'roadmap': roadmap})


# API Views
def api_roadmap_list(request):
    """API endpoint for roadmaps"""
    roadmaps = Roadmap.objects.filter(is_public=True).annotate(
        follower_count=Count('followers'),
        channel_count=Count('channels')
    ).order_by('-created_at')[:20]
    
    data = [{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'difficulty': r.difficulty,
        'estimated_hours': r.estimated_hours,
        'owner': r.owner.username,
        'follower_count': r.follower_count,
        'channel_count': r.channel_count,
        'created_at': r.created_at.isoformat(),
    } for r in roadmaps]
    
    return JsonResponse({'roadmaps': data})