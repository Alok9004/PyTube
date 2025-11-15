from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from channels.models import Channel
from videos.models import Video

class Roadmap(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='roadmaps')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    estimated_hours = models.PositiveIntegerField(default=0)
    thumbnail = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []
    
    def get_total_videos(self):
        total = 0
        for milestone in self.milestones.all():
            total += milestone.roadmap_videos.count()
        return total
    
    def get_total_duration(self):
        total = 0
        for milestone in self.milestones.all():
            total += milestone.estimated_hours
        return total

class Milestone(models.Model):
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    estimated_hours = models.PositiveIntegerField(default=0)
    is_optional = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.roadmap.title} - {self.title}"
    
    @property
    def videos_count(self):
        return self.roadmap_videos.count()

class RoadmapVideo(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='roadmap_videos')
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['milestone', 'video']
    
    def __str__(self):
        return f"{self.milestone.title} - {self.video.title}"

class UserRoadmapProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    current_milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'roadmap']
    
    def __str__(self):
        return f"{self.user.username} - {self.roadmap.title}"
    
    def get_progress_percentage(self):
        total_milestones = self.roadmap.milestones.count()
        if total_milestones == 0:
            return 0
        
        completed_milestones = UserMilestoneProgress.objects.filter(
            user=self.user,
            milestone__roadmap=self.roadmap,
            is_completed=True
        ).count()
        
        return (completed_milestones / total_milestones) * 100

class UserMilestoneProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_videos = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'milestone']
    
    def __str__(self):
        return f"{self.user.username} - {self.milestone.title}"
    
    def update_progress(self):
        total_videos = self.milestone.roadmap_videos.count()
        
        # Count completed videos (assuming VideoProgress model exists)
        try:
            from videos.models import VideoProgress
            completed_videos = VideoProgress.objects.filter(
                user=self.user,
                video__in=self.milestone.roadmap_videos.all().values_list('video', flat=True),
                watched_percentage__gte=95
            ).count()
        except:
            # Fallback if VideoProgress doesn't exist
            completed_videos = min(self.completed_videos + 1, total_videos)
        
        self.completed_videos = completed_videos
        self.is_completed = completed_videos >= total_videos
        
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.save()