from django.urls import path
from . import views

app_name = 'roadmap'

urlpatterns = [
    path('', views.roadmap_list, name='roadmap_list'),
    path('create/', views.roadmap_create, name='roadmap_create'),
    path('<int:roadmap_id>/', views.roadmap_detail, name='roadmap_detail'),
    path('<int:roadmap_id>/edit/', views.roadmap_edit, name='roadmap_edit'),
    path('<int:roadmap_id>/delete/', views.roadmap_delete, name='roadmap_delete'),
    path('<int:roadmap_id>/start/', views.start_roadmap, name='start_roadmap'),
    path('<int:roadmap_id>/progress/', views.roadmap_progress, name='roadmap_progress'),
    path('my-roadmaps/', views.my_roadmaps, name='my_roadmaps'),
    path('milestone/<int:milestone_id>/complete/', views.complete_milestone, name='complete_milestone'),
    path('search/', views.roadmap_search, name='roadmap_search'),
]