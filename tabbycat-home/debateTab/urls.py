"""
URL configuration for debateTab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from tournaments.views import UserRegistrationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tournaments.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='tournaments/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='tournaments/logout.html', next_page='/', http_method_names=['get', 'post']), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
