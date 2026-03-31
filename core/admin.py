from django.contrib import admin
from .models import GeneratedEmail

# This makes the table visible in the Admin Panel
admin.site.register(GeneratedEmail)