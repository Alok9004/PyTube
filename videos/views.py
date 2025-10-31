from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Video, VideoProgress
from .forms import VideoForm
from channels.models import Channel
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Sum
import json
# Create your views here.

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
        'progress': current_progress,  # Add this for current video progress
        'all_completed': all_completed,
        'total_duration': total_duration,
        'total_watched_seconds': total_watched_seconds,
    }

    return render(request, 'videos/detail.html', context)


@login_required
def save_progress(request, video_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_time = data.get('current_time', 0)
        new_percentage = data.get('watched_percentage', 0)

        progress, _ = VideoProgress.objects.get_or_create(
            user=request.user,
            video_id=video_id
        )

        # ✅ Only update forward (never backward)
        if new_time > progress.current_time:
            progress.current_time = new_time
        if new_percentage > progress.watched_percentage:
            progress.watched_percentage = new_percentage

        progress.last_watched = now()
        progress.save()

        return JsonResponse({
            'status': 'success',
            'current_time': progress.current_time,
            'watched_percentage': progress.watched_percentage
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)




def convert_to_embed(youtube_url):
    if "watch?v=" in youtube_url:
        video_id = youtube_url.split("v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    elif "youtu.be/" in youtube_url:
        video_id = youtube_url.split("/")[-1]
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
            # Convert YouTube URL to embed
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
        videos = Video.objects.filter(title__icontains=query)[:5]  # limit results
        for video in videos:
            results.append({
                'id': video.id,
                'title': video.title,
                'thumbnail': video.thumbnail.url if video.thumbnail else '',
            })
    return JsonResponse({'results': results})

