from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Video, VideoProgress
from .forms import VideoForm
from channels.models import Channel
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Sum
import json
import re

def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|\
youtu\.be\/|youtube\.com\/embed\/)([^&?\n]+)',
        r'youtube\.com\/watch\?.*v=([^&?\n]+)',
        r'youtu\.be\/([^&?\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def video_list(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    videos = Video.objects.filter(channel=channel).order_by('order')

    total_watched_seconds = 0
    if request.user.is_authenticated:
        total_watched_seconds = VideoProgress.objects.filter(
            user=request.user, video__in=videos
        ).aggregate(total=Sum('current_time'))['total'] or 0

    progress_dict = {}
    if request.user.is_authenticated:
        for video in videos:
            try:
                prog = VideoProgress.objects.get(user=request.user, video=video)
                progress_dict[video.id] = prog
            except VideoProgress.DoesNotExist:
                progress_dict[video.id] = None
    else:
        for video in videos:
            progress_dict[video.id] = None

    return render(request, 'videos/list.html', {
        'channel': channel,
        'videos': videos,
        'progress_dict': progress_dict,
        'total_watched_seconds': total_watched_seconds,
    })


@login_required
def video_detail(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    previous_video = video.channel.videos.filter(order__lt=video.order).order_by('-order').first()
    next_video = video.channel.videos.filter(order__gt=video.order).order_by('order').first()
    videos = video.channel.videos.all().order_by('order')

    # Extract YouTube ID for template
    youtube_id = extract_youtube_id(video.youtube_url)

    progress_dict = {}
    total_duration = 0
    total_watched_seconds = 0

    for v in videos:
        total_duration += v.duration or 0
        try:
            prog = VideoProgress.objects.get(user=request.user, video=v)
            progress_dict[v.id] = prog
            total_watched_seconds += prog.current_time
        except VideoProgress.DoesNotExist:
            progress_dict[v.id] = None

    current_progress = progress_dict.get(video.id)

    all_completed = all(
        progress_dict[v.id] and progress_dict[v.id].watched_percentage >= 95
        for v in videos
    )

    context = {
        'video': video,
        'previous_video': previous_video,
        'next_video': next_video,
        'videos': videos,
        'progress_dict': progress_dict,
        'progress': current_progress,
        'all_completed': all_completed,
        'total_duration': total_duration,
        'total_watched_seconds': total_watched_seconds,
        'youtube_id': youtube_id,  # Pass YouTube ID directly
    }

    return render(request, 'videos/detail.html', context)


@login_required
def save_progress(request, video_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_time = float(data.get('current_time', 0))
            new_percentage = float(data.get('watched_percentage', 0))

            progress, created = VideoProgress.objects.get_or_create(
                user=request.user,
                video_id=video_id
            )

            # Only update if significant progress (reduce API calls)
            time_diff = new_time - progress.current_time
            percent_diff = new_percentage - progress.watched_percentage
            
            if (time_diff >= 10 or percent_diff >= 10 or new_percentage >= 95 or created):
                progress.current_time = max(progress.current_time, new_time)
                progress.watched_percentage = max(progress.watched_percentage, new_percentage)
                progress.last_watched = now()
                progress.save()
                print(f"Progress saved: {new_time}s, {new_percentage}%")

            return JsonResponse({
                'status': 'success',
                'current_time': progress.current_time,
                'watched_percentage': progress.watched_percentage
            })
            
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Progress save error: {e}")
            return JsonResponse({'error': 'Invalid data'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def convert_to_embed(youtube_url):
    """Convert YouTube URL to embed format"""
    video_id = extract_youtube_id(youtube_url)
    if video_id:
        return f"https://www.youtube.com/embed/{video_id}"
    return youtube_url


@login_required
def video_create(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.channel = channel
            video.youtube_url = convert_to_embed(video.youtube_url)
            video.save()
            return redirect('videos:video_list', channel_id=channel.id)
    else:
        form = VideoForm()
    return render(request, 'videos/form.html', {'form': form, 'channel': channel})


@login_required
def video_edit(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        form = VideoForm(request.POST, instance=video)
        if form.is_valid():
            video = form.save(commit=False)
            video.youtube_url = convert_to_embed(video.youtube_url)
            video.save()
            return redirect('videos:video_detail', video_id=video.id)
    else:
        form = VideoForm(instance=video)
    return render(request, 'videos/form.html', {'form': form, 'video': video})


@login_required
def video_delete(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        video.delete()
        return redirect('videos:video_list', channel_id=video.channel.id)
    return render(request, 'videos/confirm_delete.html', {'video': video})


def ajax_video_search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        videos = Video.objects.filter(title__icontains=query)[:5]
        for video in videos:
            results.append({
                'id': video.id,
                'title': video.title,
                'thumbnail': video.thumbnail.url if video.thumbnail else '',
            })
    return JsonResponse({'results': results})
