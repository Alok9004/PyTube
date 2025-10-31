from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from .models import Review
from .forms import ReviewForm
from videos.models import Video

@login_required
def review_create(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    # Check if user already reviewed this video
    existing_review = Review.objects.filter(user=request.user, video=video).first()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.video = video
            review.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%b %d, %Y'),
                    'username': review.user.username
                })
            return redirect('videos:video_detail', video_id=video.id)
    else:
        form = ReviewForm(instance=existing_review)
    
    context = {
        'form': form,
        'video': video,
        'existing_review': existing_review
    }
    return render(request, 'reviews/form.html', context)

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        video_id = self.kwargs.get('video_id')
        if video_id:
            return Review.objects.filter(video_id=video_id).select_related('user')
        return Review.objects.all().select_related('user', 'video')

class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'reviews/confirm_delete.html'
    
    def test_func(self):
        return self.request.user == self.get_object().user
    
    def get_success_url(self):
        return reverse_lazy('videos:video_detail', kwargs={'video_id': self.object.video.id})

def video_reviews_stats(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    reviews = video.reviews.all()
    
    stats = {
        'total_reviews': reviews.count(),
        'average_rating': reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0,
        'rating_distribution': {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
        }
    }
    
    return JsonResponse(stats)