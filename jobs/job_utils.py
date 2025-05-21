"""
Utility functions and classes for job-related operations.
"""

from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.exceptions import APIException
from .models import Job, JobApplication, User

class JobNotFound(APIException):
    """Exception raised when a job is not found."""
    status_code = 404
    default_detail = 'Job not found.'
    default_code = 'job_not_found'

def calculate_job_stats(user: User) -> Dict[str, Any]:
    """
    Calculate job statistics for a user.
    
    Args:
        user: The user to calculate statistics for
        
    Returns:
        Dictionary containing job statistics
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

def get_cached_job_stats(request: HttpRequest) -> Dict[str, Any]:
    """
    Get cached job statistics for a user.
    
    Args:
        request: The HTTP request containing the user
        
    Returns:
        Dictionary containing cached job statistics
    """
    cache_key = f'job_stats_{request.user.id}'
    stats = cache.get(cache_key)
    
    if not stats:
        stats = calculate_job_stats(request.user)
        cache.set(cache_key, stats, timeout=300)  # Cache for 5 minutes
    
    return stats

class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job model with custom validation."""
    
    def validate_salary_range(self, value: str) -> str:
        """Validate that salary range contains numbers."""
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Salary range must contain numbers")
        return value

    def validate_deadline(self, value: timezone.datetime) -> timezone.datetime:
        """Validate that deadline is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Deadline cannot be in the past")
        return value

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('company', 'posted_date', 'views_count', 'applications_count')

def get_job_with_related(job_id: int) -> Job:
    """
    Get a job with related data using select_related and prefetch_related.
    
    Args:
        job_id: The ID of the job to retrieve
        
    Returns:
        Job object with related data
        
    Raises:
        JobNotFound: If the job does not exist
    """
    try:
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
    except Job.DoesNotExist:
        raise JobNotFound()

def get_active_jobs_with_filters(filters: Optional[Dict[str, Any]] = None) -> QuerySet:
    """
    Get active jobs with optional filters.
    
    Args:
        filters: Optional dictionary of filters to apply
        
    Returns:
        QuerySet of filtered active jobs
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