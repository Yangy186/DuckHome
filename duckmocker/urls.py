from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from duckapp.views import frontend_login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', frontend_login_view, name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('duckapp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
