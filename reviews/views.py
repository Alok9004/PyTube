from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Review
from .forms import ReviewForm
from channels.models import Channel

@login_required
def review_create(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    
    # Check if user already reviewed this channel
    existing_review = Review.objects.filter(channel=channel, user=request.user).first()
    if existing_review:
        messages.warning(request, 'You have already reviewed this channel.')
        return redirect('channels:detail', pk=channel.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.channel = channel
            review.user = request.user
            review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('channels:detail', pk=channel.id)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/form.html', {
        'form': form,
        'channel': channel,
        'title': 'Add Review'
    })

@login_required
def review_update(request, pk):
    review = get_object_or_404(Review, id=pk)
    
    # Check if user owns the review
    if review.user != request.user:
        messages.error(request, 'You can only edit your own reviews.')
        return redirect('channels:detail', pk=review.channel.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review updated successfully!')
            return redirect('channels:detail', pk=review.channel.id)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'reviews/form.html', {
        'form': form,
        'channel': review.channel,
        'title': 'Edit Review'
    })

class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'reviews/confirm_delete.html'
    
    def test_func(self):
        review = self.get_object()
        return review.user == self.request.user
    
    def get_success_url(self):
        messages.success(self.request, 'Review deleted successfully!')
        return reverse_lazy('channels:detail', kwargs={'pk': self.object.channel.id})

def review_list(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    reviews = Review.objects.filter(channel=channel).select_related('user')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    rating_count = reviews.count()
    
    # Rating distribution
    rating_dist = {}
    for i in range(1, 6):
        rating_dist[i] = reviews.filter(rating=i).count()
    
    return render(request, 'reviews/list.html', {
        'channel': channel,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_count': rating_count,
        'rating_dist': rating_dist,
    })