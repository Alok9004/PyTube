from django.urls import path
from . import views

app_name = 'channels'

urlpatterns = [
    path('', views.ChannelListView.as_view(), name='list'),
    path('create/', views.ChannelCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ChannelDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ChannelUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ChannelDeleteView.as_view(), name='delete'),
]
