from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home_view(request):

    return JsonResponse({
        "message": "ByteBrigade Backend API is running!",
        "endpoints": {
            "admin": "/admin/",
            "health": "/api/health/",
            "login": "/api/login/",
            "users": "/api/users/",
            "search": "/api/search/",
            "skills": "/api/skills/"
        },
        "status": "online",
        "version": "1.0"
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls')),
    path('', home_view, name='home'),
]
