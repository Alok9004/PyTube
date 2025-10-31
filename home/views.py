from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from videos.models import Video
from channels.models import Channel
from django.contrib.auth.models import User
from django.db.models import Q

def home(request):
    featured_channels = Channel.objects.all()[:4]  
    
    total_videos = Video.objects.count()
    total_channels = Channel.objects.count()
    total_users = User.objects.count()
    
    context = {
        'featured_channels': featured_channels,
        'total_videos': total_videos,
        'total_channels': total_channels,
        'total_users': total_users,
    }
    
    return render(request, 'home/home.html', context)



def search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        # Search in videos (title, description) and channels (name)
        video_results = Video.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        ).select_related('channel')
        
        channel_results = Channel.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
        
        results = {
            'videos': video_results,
            'channels': channel_results,
            'total_results': video_results.count() + channel_results.count()
        }
    
    return render(request, 'home/search_results.html', {
        'query': query, 
        'results': results
    })