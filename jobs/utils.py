"""
Utility functions and classes for job-related operations.
"""

from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import serializers
from .models import Job, JobApplication

def calculate_job_stats(user):
    """
    Calculate job statistics for a user.
    """
    if user.userprofile.user_type == 'employer':
        queryset = Job.objects.filter(company=user)
    else:
        queryset = Job.objects.filter(is_active=True)
    
    stats = {
        'total_jobs': queryset.count(),
        'active_jobs': queryset.filter(is_active=True).count(),
        'job_types': dict(queryset.values_list('job_type').annotate(count=Count('id'))),
        'applications': {
            'total': JobApplication.objects.filter(job__in=queryset).count(),
            'status_breakdown': dict(
                JobApplication.objects.filter(job__in=queryset)
                .values_list('status')
                .annotate(count=Count('id'))
            )
        },
        'last_updated': timezone.now()
    }
    
    return stats

class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for Job model with custom validation.
    """
    def validate_salary_range(self, value):
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Salary range must contain numbers")
        return value

    def validate_deadline(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Deadline cannot be in the past")
        return value

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('company', 'posted_date', 'views_count', 'applications_count')

def get_job_with_related(job_id):
    """
    Get a job with related data using select_related and prefetch_related.
    """
    return Job.objects.select_related(
        'company',
        'location',
        'location__country',
        'location__province',
        'location__city',
        'location__barangay'
    ).prefetch_related(
        'applications',
        'applications__applicant'
    ).get(id=job_id)

def get_active_jobs_with_filters(filters=None):
    """
    Get active jobs with optional filters.
    """
    queryset = Job.objects.select_related(
        'company',
        'location'
    ).filter(is_active=True)
    
    if filters:
        if 'job_type' in filters:
            queryset = queryset.filter(job_type=filters['job_type'])
        if 'location' in filters:
            queryset = queryset.filter(location=filters['location'])
        if 'search' in filters:
            search = filters['search']
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(requirements__icontains=search) |
                Q(company__first_name__icontains=search) |
                Q(company__last_name__icontains=search)
            )
    
    return queryset.order_by('-posted_date') 