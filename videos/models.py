from django.db import models
from channels.models import Channel
from django.contrib.auth.models import User

class Video(models.Model):
    title = models.CharField(max_length=150)
    youtube_url = models.URLField()
    order = models.PositiveIntegerField()
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='videos')
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    duration=models.FloatField(default=0.0, help_text="Video duration in seconds")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.channel.name})"


class VideoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    current_time = models.FloatField(default=0)
    watched_percentage = models.FloatField(default=0)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.username} - {self.video.title} ({self.watched_percentage:.1f}%)"