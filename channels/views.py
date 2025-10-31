# channels/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Channel
from videos.models import VideoProgress


def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    channel = self.object
    
    # ... your existing video progress code ...
    
    # Add reviews context
    reviews = channel.reviews.all()[:5]  # Show last 5 reviews
    avg_rating = channel.reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    review_count = channel.reviews.count()
    
    context['reviews'] = reviews
    context['avg_rating'] = round(avg_rating, 1)
    context['review_count'] = review_count
    context['user_has_reviewed'] = False
    
    if self.request.user.is_authenticated:
        context['user_has_reviewed'] = channel.reviews.filter(user=self.request.user).exists()
    
    return context



# -------------------------
# Create Channel
# -------------------------
@method_decorator(login_required, name='dispatch')
class ChannelCreateView(CreateView):
    model = Channel
    fields = ['name', 'description']
    template_name = 'channels/form.html'
    success_url = reverse_lazy('channels:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

# -------------------------
# List Channels
# -------------------------
class ChannelListView(ListView):
    model = Channel
    template_name = 'channels/list.html'
    context_object_name = 'channels'  # optional, for clarity in template

# -------------------------
# Channel Detail
# -------------------------
class ChannelDetailView(DetailView):
    model = Channel
    template_name = 'channels/detail.html'
    context_object_name = 'channel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.object
        videos = channel.videos.all().order_by('order')
        context['videos'] = videos

        progress_dict = {}
        completed_count = 0
        first_incomplete = None

        # Only query VideoProgress if user is authenticated
        if self.request.user.is_authenticated:
            for video in videos:
                try:
                    prog = VideoProgress.objects.get(user=self.request.user, video=video)
                    progress_dict[video.id] = prog
                    if prog.watched_percentage >= 95:
                        completed_count += 1
                    if not first_incomplete and prog.watched_percentage < 95:
                        first_incomplete = video
                except VideoProgress.DoesNotExist:
                    progress_dict[video.id] = None
                    if not first_incomplete:
                        first_incomplete = video
        else:
            # For anonymous users
            for video in videos:
                progress_dict[video.id] = None

        context['progress_dict'] = progress_dict
        context['completed_videos'] = completed_count
        context['total_videos'] = videos.count()
        context['progress_percent'] = int((completed_count / videos.count()) * 100) if videos.exists() else 0
        context['first_incomplete'] = first_incomplete

        return context
    

# -------------------------
# Update Channel
# -------------------------
class ChannelUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Channel
    fields = ['name', 'description']
    template_name = 'channels/form.html'
    success_url = reverse_lazy('channels:list')

    def test_func(self):
        # Only allow the owner of the channel to update it
        return self.request.user == self.get_object().owner

# -------------------------
# Delete Channel
# -------------------------
class ChannelDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Channel
    template_name = 'channels/confirm_delete.html'
    success_url = reverse_lazy('channels:list')

    def test_func(self):
        # Only allow the owner of the channel to delete it
        return self.request.user == self.get_object().owner
