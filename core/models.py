from django.db import models
from django.contrib.auth.models import User

# 1. GENERATED EMAILS (Updated with Schedule & Email fields)
class GeneratedEmail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    
    # Field for Bulk Campaigns & "Send Now" button
    recipient_email = models.EmailField(max_length=254, blank=True, null=True)
    
    email_purpose = models.TextField()
    tone = models.CharField(max_length=50)
    generated_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW FIELDS FOR SCHEDULING
    scheduled_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Draft') # Options: Draft, Scheduled, Sent

    def __str__(self):
        return f"Email to {self.recipient_name} ({self.company_name})"

# 2. EMAIL TEMPLATES
class EmailTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title