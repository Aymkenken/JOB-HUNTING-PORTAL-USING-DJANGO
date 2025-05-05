from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobPosting, JobApplication
from .forms import JobApplicationForm
from .notifications import send_application_status_notification, send_new_application_notification

@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    
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
            
            # Send notification to employer
            send_new_application_notification(job, request.user)
            
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobApplicationForm()
    
    return render(request, 'jobportal/apply_job.html', {
        'form': form,
        'job': job
    })

@login_required
def update_application_status(request, application_id):
    if not request.user.is_employer:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    application = get_object_or_404(JobApplication, id=application_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            # Send notification to applicant
            send_application_status_notification(application)
            
            messages.success(request, f'Application status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('employer_dashboard')

@login_required
def employer_dashboard(request):
    if not request.user.is_employer:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get all jobs posted by the employer
    jobs = JobPosting.objects.filter(employer=request.user)
    
    # Get all applications for these jobs
    applications = JobApplication.objects.filter(job__in=jobs).order_by('-created_at')
    
    return render(request, 'jobportal/employer_dashboard.html', {
        'jobs': jobs,
        'applications': applications
    })

@login_required
def applicant_dashboard(request):
    if request.user.is_employer:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get all applications by the user
    applications = JobApplication.objects.filter(applicant=request.user).order_by('-created_at')
    
    return render(request, 'jobportal/applicant_dashboard.html', {
        'applications': applications
    }) 