from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from .models import UserProfile, Job, JobApplication, Province, City, Barangay, Notification, Location, Country
from .forms import UserRegistrationForm, UserProfileForm, JobForm, JobApplicationForm, DeleteProfileForm, JobSeekerRegistrationForm, EmployerRegistrationForm
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from .custom_http_decorators import JobNotFound
import os
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
import json
from datetime import datetime, timedelta

@require_http_methods(["GET", "POST"])
def home(request):
    # If user is authenticated and has a profile, redirect to dashboard
    if request.user.is_authenticated:
        if hasattr(request.user, 'userprofile'):
            return redirect('dashboard')
    
    try:
        # Get statistics for the homepage
        active_jobs = Job.objects.filter(is_active=True).count()
        companies = UserProfile.objects.filter(user_type='employer').count()
        job_seekers = UserProfile.objects.filter(user_type='jobseeker').count()
        total_applications = JobApplication.objects.count()
        success_rate = (JobApplication.objects.filter(status='accepted').count() / 
                       max(total_applications, 1) * 100)
        
        context = {
            'active_jobs': active_jobs,
            'companies': companies,
            'job_seekers': job_seekers,
            'success_rate': round(success_rate, 1)
        }
        return render(request, 'jobs/home.html', context)
    except Exception as e:
        messages.error(request, f'Error loading homepage: {str(e)}')
        return render(request, 'jobs/home.html', {})

@require_http_methods(["GET", "POST"])
def login_view(request):
    # If user is already authenticated and has a profile, redirect to dashboard
    if request.user.is_authenticated:
        if hasattr(request.user, 'userprofile'):
            return redirect('dashboard')
        else:
            # If user is authenticated but has no profile, redirect to profile settings
            messages.warning(request, 'Please complete your profile setup.')
            return redirect('profile_settings')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if user has a profile
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    login(request, user)
                    next_url = request.GET.get('next')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('dashboard')
                except UserProfile.DoesNotExist:
                    # Create a default profile if none exists
                    UserProfile.objects.create(
                        user=user,
                        user_type='jobseeker'  # Default to jobseeker
                    )
                    login(request, user)
                    messages.info(request, 'A default profile has been created for you. Please update your profile settings.')
                    return redirect('profile_settings')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = AuthenticationForm()
    
    return render(request, 'jobs/login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home')
    return render(request, 'jobs/logout.html')

@require_http_methods(["GET"])
@login_required
def dashboard(request):
    try:
        user_profile = request.user.userprofile
        
        if user_profile.user_type == 'employer':
            # Get employer's jobs
            jobs = Job.objects.filter(company=request.user)
            posted_jobs = jobs.order_by('-posted_date')[:5]  # Get 5 most recent jobs
            
            # Calculate stats for employer
            total_jobs = jobs.count()
            active_jobs = jobs.filter(is_active=True).count()
            total_applications = JobApplication.objects.filter(job__in=jobs).count()
            total_views = jobs.aggregate(total_views=Sum('views_count'))['total_views'] or 0
            
            # Get recent applications for employer's jobs
            applications = JobApplication.objects.filter(job__in=jobs).order_by('-application_date')[:5]
            
            context = {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'total_applications': total_applications,
                'total_views': total_views,
                'posted_jobs': posted_jobs,
                'applications': applications,
                'is_employer': True,
                'user_profile': user_profile
            }
            
        else:  # Job seeker
            # Get job seeker's applications
            applications = JobApplication.objects.filter(applicant=request.user).order_by('-application_date')[:5]
            
            # Calculate stats for job seeker
            total_jobs = Job.objects.filter(is_active=True).count()
            active_jobs = total_jobs
            total_applications = applications.count()
            total_views = 0  # Profile views not implemented yet
            
            # Get recommended jobs (jobs that match job seeker's profile)
            recommended_jobs = Job.objects.filter(
                is_active=True
            ).exclude(
                applications__applicant=request.user  # Exclude jobs already applied to
            ).order_by('-posted_date')[:6]  # Get 6 most recent jobs
            
            context = {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'total_applications': total_applications,
                'total_views': total_views,
                'posted_jobs': recommended_jobs,  # Show recommended jobs
                'applications': applications,
                'is_jobseeker': True,
                'user_profile': user_profile
            }
        
        return render(request, 'jobs/dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('profile_settings')

@require_http_methods(["GET", "POST"])
def register_choice(request):
    """View for the account type selection page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'jobs/register_choice.html')

def register_jobseeker(request):
    """View for job seeker registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = JobSeekerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile for job seeker
            UserProfile.objects.create(
                user=user,
                user_type='jobseeker'
            )
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to JobPoint Surigao.')
            return redirect('dashboard')
    else:
        form = JobSeekerRegistrationForm()
    return render(request, 'jobs/register_jobseeker.html', {'form': form})

def register_employer(request):
    """View for employer registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = EmployerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile for employer
            UserProfile.objects.create(
                user=user,
                user_type='employer',
                company_name=form.cleaned_data.get('company_name'),
                company_website=form.cleaned_data.get('company_website'),
                bio=form.cleaned_data.get('bio')
            )
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to JobPoint Surigao.')
            return redirect('dashboard')
    else:
        form = EmployerRegistrationForm()
    return render(request, 'jobs/register_employer.html', {'form': form})

@login_required
def profile_settings(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Create a new profile if it doesn't exist
        user_profile = UserProfile.objects.create(
            user=request.user,
            user_type='jobseeker'  # Default to jobseeker
        )
    
    if request.method == 'POST':
        if 'current_password' in request.POST:
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
            return redirect('profile_settings')
            
        elif 'confirm_delete' in request.POST:
            # Handle account deletion
            password = request.POST.get('password')
            if not request.user.check_password(password):
                messages.error(request, 'Password is incorrect.')
            else:
                request.user.delete()
                messages.success(request, 'Your account has been deleted successfully.')
                return redirect('home')
            return redirect('profile_settings')
    
    return render(request, 'jobs/profile_settings.html', {
        'user_profile': user_profile
    })

@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Create a new profile if it doesn't exist
        user_profile = UserProfile.objects.create(
            user=request.user,
            user_type='jobseeker'  # Default to jobseeker
        )
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'jobs/profile.html', {
        'form': form,
        'user_profile': user_profile
    })

@require_http_methods(["GET", "POST"])
@login_required
def post_job(request):
    # Debug: Print user type and check
    user_type = request.user.userprofile.user_type
    print(f"Debug - User: {request.user.username}, Type: {user_type}")
    
    if user_type != 'employer':
        print(f"Debug - Access denied. User type is: {user_type}")
        messages.error(request, 'Only employers can post jobs.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            try:
                job = form.save(commit=False)
                job.company = request.user
                # Set contact information from form data
                job.contact_email = form.cleaned_data.get('contact_email')
                job.contact_number = form.cleaned_data.get('contact_number')
                job.save()
                messages.success(request, 'Job posted successfully!')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error posting job: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = JobForm()
    
    return render(request, 'jobs/post_job.html', {'form': form})

def job_list(request):
    query = request.GET.get('q')
    job_type = request.GET.get('job_type')
    location_id = request.GET.get('location')
    sort_by = request.GET.get('sort', '-posted_date')
    
    # Get all active jobs
    jobs = Job.objects.filter(is_active=True)
    
    # Search functionality
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(requirements__icontains=query) |
            Q(company__first_name__icontains=query) |
            Q(company__last_name__icontains=query) |
            Q(location__city__name__icontains=query) |
            Q(location__province__name__icontains=query)
        )
    
    # Filter by job type
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    # Filter by location
    if location_id:
        jobs = jobs.filter(location_id=location_id)
    
    # Sort jobs
    valid_sort_fields = {
        '-posted_date': 'Newest First',
        'posted_date': 'Oldest First',
        'title': 'Title (A-Z)',
        '-title': 'Title (Z-A)',
        'salary_range': 'Salary (Low to High)',
        '-salary_range': 'Salary (High to Low)',
        'deadline': 'Deadline (Soonest)',
        '-deadline': 'Deadline (Latest)'
    }
    
    if sort_by not in valid_sort_fields:
        sort_by = '-posted_date'
    
    jobs = jobs.order_by(sort_by)
    
    # Get all locations for the filter dropdown
    locations = Location.objects.all().order_by('country__name', 'province__name', 'city__name', 'barangay__name')
    
    # Get job statistics
    total_jobs = jobs.count()
    job_types_count = dict(Job.objects.filter(is_active=True).values_list('job_type').annotate(count=models.Count('id')))
    
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'jobs': page_obj,
        'job_types': Job.JOB_TYPE_CHOICES,
        'locations': locations,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'total_jobs': total_jobs,
        'job_types_count': job_types_count,
        'sort_options': valid_sort_fields,
        'current_sort': sort_by,
        'search_query': query,
        'selected_job_type': job_type,
        'selected_location': location_id
    }
    
    return render(request, 'jobs/job_list.html', context)

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the job poster
    if job.company != request.user:
        return HttpResponseForbidden("You don't have permission to edit this job.")
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            # Update contact information
            job.contact_email = form.cleaned_data.get('contact_email')
            job.contact_number = form.cleaned_data.get('contact_number')
            job.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('dashboard')
    else:
        form = JobForm(instance=job)
    
    return render(request, 'jobs/edit_job.html', {
        'form': form,
        'job': job
    })

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the job poster
    if job.company != request.user:
        return HttpResponseForbidden("You don't have permission to delete this job.")
    
    job.delete()
    messages.success(request, 'Job deleted successfully!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('dashboard')

@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the job poster
    if job.company != request.user:
        return HttpResponseForbidden("You don't have permission to view these applications.")
    
    applications = JobApplication.objects.filter(job=job).order_by('-application_date')
    
    return render(request, 'jobs/job_applications.html', {
        'job': job,
        'applications': applications
    })

@require_http_methods(["GET", "POST"])
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is a job seeker
    if request.user.userprofile.user_type != 'jobseeker':
        return HttpResponseForbidden("Only job seekers can apply for jobs.")
    
    # Check if user has already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', job_id=job.id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.status = 'pending'
            application.save()
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobApplicationForm()
    
    return render(request, 'jobs/apply_job.html', {
        'job': job,
        'form': form
    })

@require_http_methods(["GET", "POST"])
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
            
            try:
                # Send notification to applicant
                channel_layer = get_channel_layer()
                if channel_layer:
                    room_name = f"notifications_{application.applicant.id}"
                    
                    async_to_sync(channel_layer.group_send)(
                        room_name,
                        {
                            "type": "notification_message",
                            "message": {
                                "type": "application_status",
                                "job_title": application.job.title,
                                "status": status,
                                "job_id": application.job.id,
                                "application_id": application.id
                            }
                        }
                    )
                else:
                    print("Channel layer not available")
            except Exception as e:
                print(f"Error sending notification: {str(e)}")
                # Don't let notification errors affect the main functionality
                pass
            
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
def manage_jobs(request):
    """View for managing posted jobs"""
    jobs = Job.objects.filter(company=request.user).order_by('-posted_date')
    return render(request, 'jobs/manage_jobs.html', {'jobs': jobs})

@require_GET
@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]
    data = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'link': n.link
    } for n in notifications]
    return JsonResponse({'notifications': data})

@require_POST
@login_required
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

@require_POST
@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@login_required
def manage_locations(request):
    locations = Location.objects.all().order_by('country__name', 'province__name', 'city__name', 'barangay__name')
    return render(request, 'jobs/manage_locations.html', {'locations': locations})

@require_http_methods(["GET", "POST"])
@login_required
def add_location(request):
    if request.method == 'POST':
        country_id = request.POST.get('country')
        province_id = request.POST.get('province')
        city_id = request.POST.get('city')
        barangay_id = request.POST.get('barangay')
        
        try:
            location = Location.objects.create(
                country_id=country_id,
                province_id=province_id,
                city_id=city_id,
                barangay_id=barangay_id
            )
            messages.success(request, 'Location added successfully.')
            return redirect('manage_locations')
        except Exception as e:
            messages.error(request, f'Error adding location: {str(e)}')
    
    countries = Country.objects.all().order_by('name')
    return render(request, 'jobs/add_location.html', {'countries': countries})

@require_POST
@login_required
def delete_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    
    if request.method == 'POST':
        try:
            location.delete()
            messages.success(request, 'Location deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting location: {str(e)}')
    
    return redirect('manage_locations')

def delete_profile(request):
    if request.method == 'POST':
        form = DeleteProfileForm(request.user, request.POST)
        if form.is_valid():
            # Delete the user's profile and account
            user = request.user
            logout(request)  # Log out the user
            user.delete()  # This will also delete the associated UserProfile due to CASCADE
            messages.success(request, 'Your profile has been successfully deleted.')
            return redirect('home')
    else:
        form = DeleteProfileForm(request.user)
    
    return render(request, 'jobs/delete_profile.html', {'form': form})

@require_http_methods(["GET", "POST"])
@login_required
def update_profile_type(request):
    try:
        user_profile = request.user.userprofile
        user_profile.user_type = 'employer'
        user_profile.save()
        messages.success(request, 'Your profile has been updated to employer type.')
    except Exception as e:
        messages.error(request, f'Error updating profile: {str(e)}')
    return redirect('dashboard')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_settings')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'jobs/profile_settings.html', {
        'form': form,
        'user_profile': request.user.userprofile
    })

def application_list(request):
    return HttpResponse("Application list coming soon.")

def application_detail(request, application_id):
    from django.http import HttpResponse
    return HttpResponse(f"Application detail for ID {application_id} coming soon.")

@login_required
def view_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Check if user is the job poster
    if application.job.company != request.user:
        return HttpResponseForbidden("You don't have permission to view this application.")
    
    return render(request, 'jobs/view_application.html', {
        'application': application
    })

@require_http_methods(["POST"])
@login_required
def update_application_status(request, application_id):
    try:
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Check if user is the job poster
        if application.job.company != request.user:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in dict(JobApplication.STATUS_CHOICES):
            return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
        
        # Update the application status
        application.status = new_status
        application.save()
        
        # Send notification to applicant
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                room_name = f"notifications_{application.applicant.id}"
                async_to_sync(channel_layer.group_send)(
                    room_name,
                    {
                        "type": "notification_message",
                        "message": {
                            "type": "application_status",
                            "job_title": application.job.title,
                            "status": new_status,
                            "job_id": application.job.id,
                            "application_id": application.id
                        }
                    }
                )
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            # Don't let notification errors affect the main functionality
        
        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {new_status}',
            'new_status': new_status
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
def toggle_theme(request):
    try:
        data = json.loads(request.body)
        theme = data.get('theme')
        
        if theme not in ['light', 'dark', 'system']:
            return JsonResponse({'error': 'Invalid theme'}, status=400)
            
        user_profile = request.user.userprofile
        user_profile.theme = theme
        user_profile.save()
        
        return JsonResponse({
            'success': True,
            'theme': theme
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    has_applied = False
    
    if request.user.is_authenticated and request.user.userprofile.user_type == 'jobseeker':
        has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
    
    context = {
        'job': job,
        'has_applied': has_applied
    }
    return render(request, 'jobs/job_detail.html', context)

@require_http_methods(["GET"])
@login_required
def dashboard_stats(request):
    """View for getting dashboard statistics."""
    try:
        user_profile = request.user.userprofile
        
        if user_profile.user_type == 'employer':
            # Employer stats
            jobs = Job.objects.filter(company=request.user)
            total_jobs = jobs.count()
            active_jobs = jobs.filter(is_active=True).count()
            total_applications = JobApplication.objects.filter(job__in=jobs).count()
            total_views = jobs.aggregate(total_views=Sum('views_count'))['total_views'] or 0
        else:
            # Job seeker stats
            applications = JobApplication.objects.filter(applicant=request.user)
            total_jobs = Job.objects.filter(is_active=True).count()
            active_jobs = total_jobs
            total_applications = applications.count()
            total_views = 0  # Job seekers don't have job views

        return JsonResponse({
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'total_views': total_views
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def employer_applications(request):
    """View for employers to manage all applications across their jobs."""
    if request.user.userprofile.user_type != 'employer':
        return HttpResponseForbidden("Only employers can access this page.")
    
    # Get all jobs posted by the employer
    jobs = Job.objects.filter(company=request.user)
    
    # Get all applications for these jobs
    applications = JobApplication.objects.filter(job__in=jobs)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status and status in dict(JobApplication.STATUS_CHOICES):
        applications = applications.filter(status=status)
    
    # Filter by job if provided
    job_id = request.GET.get('job')
    if job_id:
        applications = applications.filter(job_id=job_id)
    
    # Sort applications
    sort_by = request.GET.get('sort', '-application_date')
    if sort_by in ['application_date', '-application_date', 'status', '-status']:
        applications = applications.order_by(sort_by)
    
    # Paginate results
    paginator = Paginator(applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'jobs': jobs,
        'status_choices': JobApplication.STATUS_CHOICES,
        'current_status': status,
        'current_job': job_id,
        'current_sort': sort_by,
    }
    
    return render(request, 'jobs/employer_applications.html', context)

@login_required
def employer_analytics(request):
    if request.user.userprofile.user_type != 'employer':
        return HttpResponseForbidden("Access denied")
    
    # Get date range from request or default to last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get all jobs posted by the employer
    jobs = Job.objects.filter(company=request.user)
    
    # Get all applications for these jobs
    applications = JobApplication.objects.filter(job__in=jobs)
    
    # Calculate basic statistics
    total_jobs = jobs.count()
    total_applications = applications.count()
    active_jobs = jobs.filter(is_active=True).count()
    
    # Calculate application status distribution
    status_distribution = applications.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Calculate applications over time (last 30 days)
    applications_over_time = applications.filter(
        application_date__gte=start_date
    ).values('application_date').annotate(
        count=Count('id')
    ).order_by('application_date')
    
    # Calculate top jobs by number of applications
    top_jobs = jobs.annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:5]
    
    context = {
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'active_jobs': active_jobs,
        'status_distribution': status_distribution,
        'applications_over_time': list(applications_over_time),
        'top_jobs': top_jobs,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'jobs/employer_analytics.html', context)

@login_required
def employer_analytics_data(request):
    if request.user.userprofile.user_type != 'employer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get date range from request
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get all jobs posted by the employer
    jobs = Job.objects.filter(company=request.user)
    
    # Get all applications for these jobs
    applications = JobApplication.objects.filter(job__in=jobs)
    
    # Calculate application status distribution
    status_distribution = list(applications.values('status').annotate(
        count=Count('id')
    ).order_by('status'))
    
    # Calculate applications over time
    applications_over_time = list(applications.filter(
        application_date__gte=start_date
    ).values('application_date').annotate(
        count=Count('id')
    ).order_by('application_date'))
    
    # Calculate top jobs by number of applications
    top_jobs = list(jobs.annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:5].values('title', 'application_count'))
    
    return JsonResponse({
        'status_distribution': status_distribution,
        'applications_over_time': applications_over_time,
        'top_jobs': top_jobs,
    })