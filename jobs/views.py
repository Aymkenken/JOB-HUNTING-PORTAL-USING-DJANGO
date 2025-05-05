from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import UserProfile, Job, JobApplication, Province, City, Barangay
from .forms import UserRegistrationForm, UserProfileForm, JobForm, JobApplicationForm
from django.contrib.auth.forms import AuthenticationForm

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'jobs/home.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'jobs/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def dashboard(request):
    user_profile = request.user.userprofile
    if user_profile.user_type == 'employer':
        posted_jobs = Job.objects.filter(company=request.user)
        applications = JobApplication.objects.filter(job__company=request.user)
        return render(request, 'jobs/dashboard.html', {
            'user_profile': user_profile,
            'posted_jobs': posted_jobs,
            'applications': applications
        })
    else:
        applied_jobs = JobApplication.objects.filter(applicant=request.user)
        return render(request, 'jobs/dashboard.html', {
            'user_profile': user_profile,
            'applied_jobs': applied_jobs
        })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'jobs/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    return render(request, 'jobs/profile.html', {'form': form})

@login_required
def post_job(request):
    if request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Only employers can post jobs.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('dashboard')
    else:
        form = JobForm()
    return render(request, 'jobs/post_job.html', {'form': form})

def job_list(request):
    query = request.GET.get('q')
    job_type = request.GET.get('job_type')
    location = request.GET.get('location')
    
    jobs = Job.objects.filter(is_active=True)
    
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(requirements__icontains=query)
        )
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'jobs/job_list.html', {
        'jobs': page_obj,
        'job_types': Job.JOB_TYPE_CHOICES,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    })

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    already_applied = False
    
    if request.user.is_authenticated:
        already_applied = JobApplication.objects.filter(
            job=job,
            applicant=request.user
        ).exists()
    
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied
    })

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.user.userprofile.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('job_detail', job_id=job_id)
    
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('job_detail', job_id=job_id)
    else:
        form = JobApplicationForm()
    
    return render(request, 'jobs/apply_job.html', {
        'form': form,
        'job': job
    })

@login_required
def manage_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    if request.user != application.job.company:
        messages.error(request, 'You are not authorized to manage this application.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(JobApplication.STATUS_CHOICES):
            application.status = status
            application.save()
            messages.success(request, 'Application status updated successfully!')
        return redirect('dashboard')
    
    return render(request, 'jobs/manage_application.html', {
        'application': application
    })

@require_http_methods(["GET"])
def load_provinces(request):
    country_id = request.GET.get('country_id')
    if country_id:
        provinces = Province.objects.filter(country_id=country_id).order_by('name')
        data = [{'id': p.id, 'name': p.name} for p in provinces]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

@require_http_methods(["GET"])
def load_cities(request):
    province_id = request.GET.get('province_id')
    if province_id:
        cities = City.objects.filter(province_id=province_id).order_by('name')
        data = [{'id': c.id, 'name': c.name} for c in cities]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

@require_http_methods(["GET"])
def load_barangays(request):
    city_id = request.GET.get('city_id')
    if city_id:
        barangays = Barangay.objects.filter(city_id=city_id).order_by('name')
        data = [{'id': b.id, 'name': b.name} for b in barangays]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

@login_required
def toggle_theme(request):
    if request.method == 'POST':
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.theme = 'dark' if user_profile.theme == 'light' else 'light'
            user_profile.save()
            return JsonResponse({'success': True, 'theme': user_profile.theme})
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User profile not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})