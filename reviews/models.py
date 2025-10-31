from django.db import models
from django.contrib.auth.models import User
from channels.models import Channel
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('channel', 'user')  # One review per user per channel
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.channel.name} ({self.rating}★)"