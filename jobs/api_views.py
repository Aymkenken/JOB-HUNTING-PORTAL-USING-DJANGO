from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.db import transaction
from .models import Job, JobApplication, UserProfile, Location
from .serializers import (
    UserProfileSerializer, JobSerializer, 
    JobApplicationSerializer, LocationSerializer
)
import os
from datetime import datetime

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number
        })

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserProfile.objects.filter(user=self.request.user)
        return UserProfile.objects.none()

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_active=True)
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'company', 'location']
    search_fields = ['title', 'description', 'requirements']
    ordering_fields = ['posted_date', 'deadline', 'salary_range']

    def perform_create(self, serializer):
        serializer.save(company=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            serializer.save(company=self.request.user)
        except Exception as e:
            raise ValidationError(f"Error creating job: {str(e)}")

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        try:
            job = self.get_object()
            
            # Check if job is still active
            if not job.is_active:
                return Response(
                    {'error': 'This job posting is no longer active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if deadline has passed
            if job.deadline < timezone.now().date():
                return Response(
                    {'error': 'The application deadline for this job has passed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has already applied
            if JobApplication.objects.filter(job=job, applicant=request.user).exists():
                return Response(
                    {'error': 'You have already applied for this job'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate resume file
            resume = request.FILES.get('resume')
            if not resume:
                return Response(
                    {'error': 'Resume is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (5MB limit)
            if resume.size > 5 * 1024 * 1024:
                return Response(
                    {'error': 'Resume file size must be less than 5MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file type
            valid_extensions = ['.pdf', '.doc', '.docx']
            ext = os.path.splitext(resume.name)[1].lower()
            if ext not in valid_extensions:
                return Response(
                    {'error': 'Resume must be a PDF or Word document'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                serializer = JobApplicationSerializer(data={
                    'job': job.id,
                    'applicant': request.user.id,
                    'resume': resume,
                    'cover_letter': request.data.get('cover_letter', '')
                })
                
                if serializer.is_valid():
                    application = serializer.save()
                    job.applications_count += 1
                    job.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied:
            return Response(
                {'error': 'You do not have permission to perform this action'},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            if request.user.userprofile.user_type == 'employer':
                queryset = self.get_queryset().filter(company=request.user)
            else:
                queryset = self.get_queryset()
                
            total_jobs = queryset.count()
            active_jobs = queryset.filter(is_active=True).count()
            job_types = queryset.values('job_type').annotate(count=Count('id'))
            
            return Response({
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'job_types': job_types,
                'last_updated': timezone.now()
            })
        except Exception as e:
            return Response(
                {'error': f'Error getting stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job', 'applicant', 'status']
    ordering_fields = ['application_date', 'last_updated']

    def get_queryset(self):
        user = self.request.user
        if user.userprofile.user_type == 'employer':
            return JobApplication.objects.filter(job__company=user)
        return JobApplication.objects.filter(applicant=user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        try:
            application = self.get_object()
            
            # Only employers can update application status
            if request.user.userprofile.user_type != 'employer':
                return Response(
                    {'error': 'Only employers can update application status'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            new_status = request.data.get('status')
            if new_status not in dict(JobApplication.STATUS_CHOICES):
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                application.status = new_status
                application.save()
                
                # Update job statistics if needed
                if new_status == 'accepted':
                    application.job.applications_count += 1
                    application.job.save()
            
            return Response(JobApplicationSerializer(application).data)
        except Exception as e:
            return Response(
                {'error': f'Error updating application status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            if request.user.userprofile.user_type == 'employer':
                queryset = JobApplication.objects.filter(job__company=request.user)
            else:
                queryset = JobApplication.objects.filter(applicant=request.user)
                
            total_applications = queryset.count()
            status_counts = {
                status: queryset.filter(status=status).count()
                for status, _ in JobApplication.STATUS_CHOICES
            }
            
            return Response({
                'total_applications': total_applications,
                'status_breakdown': status_counts,
                'last_updated': timezone.now()
            })
        except Exception as e:
            return Response(
                {'error': f'Error getting application stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'province', 'city', 'barangay']
    ordering_fields = ['country__name', 'province__name', 'city__name', 'barangay__name'] 