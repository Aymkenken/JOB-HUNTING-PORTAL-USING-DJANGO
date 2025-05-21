from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Job, JobApplication, Location

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'user_type', 'phone_number', 'address', 'bio', 'profile_picture', 'theme')
        read_only_fields = ('id',)

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'country', 'province', 'city', 'barangay')

class JobSerializer(serializers.ModelSerializer):
    company = UserSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    
    class Meta:
        model = Job
        fields = ('id', 'title', 'company', 'job_type', 'location', 'description', 
                 'requirements', 'salary_range', 'posted_date', 'deadline', 
                 'is_active', 'views_count', 'applications_count')
        read_only_fields = ('id', 'posted_date', 'views_count', 'applications_count')

class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    applicant = UserSerializer(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = ('id', 'job', 'applicant', 'cover_letter', 'resume', 
                 'application_date', 'status', 'last_updated')
        read_only_fields = ('id', 'application_date', 'last_updated') 