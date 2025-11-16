from django.db import models
from django.contrib.auth.models import User
from channels.models import Channel

class Roadmap(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_roadmaps')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    estimated_hours = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    followers = models.ManyToManyField(User, through='RoadmapFollow', related_name='followed_roadmaps')
    
    def __str__(self):
        return self.title
    
    def total_channels(self):
        return self.channels.count()
    
    def total_followers(self):
        return self.followers.count()

class RoadmapChannel(models.Model):
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='channels')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['roadmap', 'channel']
    
    def __str__(self):
        return f"{self.roadmap.title} - {self.channel.name}"

class RoadmapFollow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_channel_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'roadmap']
    
    def progress_percentage(self):
        total_channels = self.roadmap.channels.count()
        if total_channels == 0:
            return 0
        return int((self.current_channel_order / total_channels) * 100)
    
    def is_completed(self):
        return self.completed_at is not None