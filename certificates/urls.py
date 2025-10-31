from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('download/<int:channel_id>/', views.certificate_download, name='download'),
]
