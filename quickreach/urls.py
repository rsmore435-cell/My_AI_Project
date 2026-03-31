from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # This points to your 'core' app. Do NOT import views here.
    path('', include('core.urls')), 
]