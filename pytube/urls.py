from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('channels/', include(('channels.urls', 'channels'), namespace='channels')),
    path('videos/', include(('videos.urls', 'videos'), namespace='videos')),
    path('roadmaps/', include('roadmaps.urls')),
    path('', include(('home.urls'), namespace='home')),
]
