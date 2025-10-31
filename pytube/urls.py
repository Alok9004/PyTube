from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('channels/', include(('channels.urls', 'channels'), namespace='channels')),
    path('videos/', include(('videos.urls', 'videos'), namespace='videos')),
    path('', include(('home.urls'), namespace='home')),
    # path('certificates/', include('certificates.urls')),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

