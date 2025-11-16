from django.contrib import admin
from .models import Roadmap, RoadmapChannel, RoadmapFollow

@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'difficulty', 'estimated_hours', 'is_public', 'created_at', 'total_followers']
    list_filter = ['difficulty', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RoadmapChannel)
class RoadmapChannelAdmin(admin.ModelAdmin):
    list_display = ['roadmap', 'channel', 'order']
    list_filter = ['roadmap']
    search_fields = ['roadmap__title', 'channel__name']

@admin.register(RoadmapFollow)
class RoadmapFollowAdmin(admin.ModelAdmin):
    list_display = ['user', 'roadmap', 'started_at', 'completed_at', 'current_channel_order']
    list_filter = ['started_at', 'completed_at']
    search_fields = ['user__username', 'roadmap__title']
    readonly_fields = ['started_at']