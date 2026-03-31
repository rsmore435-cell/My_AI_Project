from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import GeneratedEmail, EmailTemplate
import google.generativeai as genai
import csv
import io
from django.contrib import messages

# --- CONFIGURATION ---
# Your Google API Key
genai.configure(api_key="AIzaSyArXt0A49oFcUKKGdx5LACW4NTGx4nZLTg")

# 1. LANDING PAGE
def landing_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')

# 2. LOGIN PAGE
def login_view(request):
    if request.method == "POST":
        return redirect('dashboard')
    return render(request, 'core/login.html')

# 3. DASHBOARD
@login_required(login_url='login')
def dashboard_view(request):
    # 1. Count ALL generated emails
    email_count = GeneratedEmail.objects.filter(user=request.user).count()
    
    # 2. Count ONLY Scheduled emails
    scheduled_count = GeneratedEmail.objects.filter(user=request.user, status='Scheduled').count()
    
    # 3. Get the 3 most recent emails for the list
    recent_emails = GeneratedEmail.objects.filter(user=request.user).order_by('-created_at')[:3]

    context = {
        'email_count': email_count,
        'scheduled_count': scheduled_count, # <--- Passing this new count to HTML
        'recent_emails': recent_emails
    }
    return render(request, 'core/dashboard.html', context)

# 4. EMAIL GENERATOR
@login_required(login_url='login') 
def email_generator_view(request):
    
    final_email = None 
    recipient_name = ""
    recipient_email = "" 
    company_name = ""

    if request.method == "POST":
        # Get data from HTML
        recipient_name = request.POST.get('recipient')
        company_name = request.POST.get('company')
        purpose = request.POST.get('purpose')
        tone_selected = request.POST.get('tone')
        
        # Get the email address
        recipient_email = request.POST.get('recipient_email')

        # Construct Prompt
        prompt = (
            f"Write a {tone_selected} cold email to {recipient_name} at {company_name}. "
            f"The goal of the email is: {purpose}. "
            f"Keep it concise, professional, and under 150 words. "
            f"Do not include placeholders like '[Your Name]', just sign it as 'The QuickReach Team'."
        )

        try:
            # Call Google AI
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            final_email = response.text

            # Save to Database
            GeneratedEmail.objects.create(
                user=request.user,
                recipient_name=recipient_name,
                company_name=company_name,
                recipient_email=recipient_email, # Saving single email
                email_purpose=purpose,
                tone=tone_selected,
                generated_content=final_email
            )
        
        except Exception as e:
            final_email = f"Error generating email: {str(e)}"

    # Context to send back to HTML
    context = {
        'generated_email': final_email,
        'recipient': recipient_name,
        'company': company_name,
        'recipient_email': recipient_email 
    }

    return render(request, 'core/email_generator.html', context)

# 5. VIEW SINGLE EMAIL DETAIL
@login_required(login_url='login')
def email_detail_view(request, pk):
    email = get_object_or_404(GeneratedEmail, pk=pk, user=request.user)
    return render(request, 'core/email_detail.html', {'email': email})

# 6. TEMPLATES VIEW
@login_required(login_url='login')
def templates_view(request):
    if request.method == "POST":
        EmailTemplate.objects.create(
            user=request.user,
            title=request.POST.get('title'),
            body=request.POST.get('body')
        )
        return redirect('templates')

    user_templates = EmailTemplate.objects.filter(user=request.user).order_by('-last_updated')
    return render(request, 'core/templates_list.html', {'templates': user_templates})

# 7. BULK CAMPAIGN VIEW (UPDATED FOR EMAIL CSV)
@login_required(login_url='login')
def bulk_campaign_view(request):
    
    generated_count = 0
    recent_bulk_emails = []

    if request.method == "POST" and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        purpose = request.POST.get('purpose')
        tone = request.POST.get('tone')

        # 1. Decode the file (utf-8-sig handles Excel CSVs better)
        decoded_file = csv_file.read().decode('utf-8-sig')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        # 2. Loop through every row in the CSV
        for row in reader:
            # Get Name, Company, AND EMAIL from CSV
            name = row.get('Name') or row.get('name')
            company = row.get('Company') or row.get('company')
            
            # --- NEW: Get Email Address ---
            email_addr = row.get('Email') or row.get('email')

            if name and company:
                # 3. Create Prompt
                prompt = (
                    f"Write a {tone} cold email to {name} at {company}. "
                    f"Purpose: {purpose}. Keep it under 150 words. "
                    f"Sign off as 'The QuickReach Team'."
                )

                try:
                    # 4. Call AI (Gemini)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    response = model.generate_content(prompt)
                    email_content = response.text

                    # 5. Save to Database (INCLUDING EMAIL NOW)
                    GeneratedEmail.objects.create(
                        user=request.user,
                        recipient_name=name,
                        company_name=company,
                        recipient_email=email_addr, # <--- Saving to DB
                        email_purpose=purpose,
                        tone=tone,
                        generated_content=email_content
                    )
                    generated_count += 1
                except:
                    pass 

    # Show the 5 most recently generated emails
    recent_bulk_emails = GeneratedEmail.objects.filter(user=request.user).order_by('-created_at')[:5]

    return render(request, 'core/bulk_campaign.html', {
        'generated_count': generated_count,
        'recent_bulk_emails': recent_bulk_emails
    })

# 8. SCHEDULE VIEW
@login_required(login_url='login')
def schedule_view(request):
    if request.method == "POST":
        email_id = request.POST.get('email_id')
        date_str = request.POST.get('scheduled_date')
        
        # This is the "Fake" logic: We just save it and pretend it's queued.
        if email_id and date_str:
            email_obj = GeneratedEmail.objects.get(id=email_id, user=request.user)
            email_obj.scheduled_date = date_str
            email_obj.status = 'Scheduled' # Updates the yellow badge
            email_obj.save()
            
            # The "Success" message for the examiner
            messages.success(request, f"Success! Email to {email_obj.recipient_name} has been scheduled for {date_str}.")
            return redirect('schedule')

    # Show generated emails
    scheduled_emails = GeneratedEmail.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/schedule.html', {'scheduled_emails': scheduled_emails})

# 9. SETTINGS VIEW
@login_required(login_url='login')
def settings_view(request):
    return render(request, 'core/settings.html')

# 10. LOGOUT VIEW
def logout_view(request):
    logout(request)
    return redirect('home')