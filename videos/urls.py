from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('<int:channel_id>/', views.video_list, name='video_list'),
    path('detail/<int:video_id>/', views.video_detail, name='video_detail'),
    path('<int:channel_id>/create/', views.video_create, name='video_create'),
    path('<int:video_id>/edit/', views.video_edit, name='video_edit'),
    path('<int:video_id>/delete/', views.video_delete, name='video_delete'),
    path('save_progress/<int:video_id>/', views.save_progress, name='save_progress'),
    path('ajax_search/', views.ajax_video_search, name='ajax_search'),
]

