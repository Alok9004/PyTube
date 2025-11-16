from django.urls import path
from . import views

app_name = 'roadmaps'

urlpatterns = [
    path('', views.RoadmapListView.as_view(), name='list'),
    path('categories/', views.roadmap_categories, name='categories'),
    path('create/', views.RoadmapCreateView.as_view(), name='create'),
    path('<int:pk>/', views.RoadmapDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.RoadmapUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.RoadmapDeleteView.as_view(), name='delete'),
    
    path('<int:roadmap_id>/add-channel/', views.add_channel_to_roadmap, name='add_channel'),
    path('<int:roadmap_id>/remove-channel/<int:channel_id>/', views.remove_channel_from_roadmap, name='remove_channel'),
    
    path('<int:roadmap_id>/follow/', views.follow_roadmap, name='follow'),
    path('<int:roadmap_id>/unfollow/', views.unfollow_roadmap, name='unfollow'),
    path('<int:roadmap_id>/update-progress/', views.update_roadmap_progress, name='update_progress'),
    path('<int:roadmap_id>/auto-update/', views.auto_update_progress, name='auto_update'),
    path('<int:roadmap_id>/reset/', views.reset_progress, name='reset_progress'),
    
    path('my-roadmaps/', views.my_roadmaps, name='my_roadmaps'),
    path('recommendations/', views.roadmap_recommendations, name='recommendations'),
    path('stats/', views.roadmap_stats, name='stats'),
    
    path('api/list/', views.api_roadmap_list, name='api_list'),
]