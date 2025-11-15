from django.contrib import admin
from .models import Roadmap, Milestone, RoadmapVideo, UserRoadmapProgress, UserMilestoneProgress

@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel', 'level', 'status', 'is_featured', 'created_by', 'created_at']
    list_filter = ['level', 'status', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'roadmap', 'order', 'videos_count', 'estimated_hours']
    list_filter = ['roadmap']
    search_fields = ['title', 'description']

@admin.register(RoadmapVideo)
class RoadmapVideoAdmin(admin.ModelAdmin):
    list_display = ['milestone', 'video', 'order', 'is_required']
    list_filter = ['milestone', 'is_required']

@admin.register(UserRoadmapProgress)
class UserRoadmapProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'roadmap', 'started_at', 'completed_at', 'is_completed']
    list_filter = ['is_completed', 'started_at']
    readonly_fields = ['started_at']

@admin.register(UserMilestoneProgress)
class UserMilestoneProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'milestone', 'started_at', 'completed_at', 'completed_videos', 'is_completed']
    list_filter = ['is_completed']
    readonly_fields = ['started_at']