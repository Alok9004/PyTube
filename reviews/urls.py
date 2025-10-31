from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('channel/<int:channel_id>/', views.review_list, name='list'),
    path('channel/<int:channel_id>/create/', views.review_create, name='create'),
    path('<int:pk>/edit/', views.review_update, name='update'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete'),
]