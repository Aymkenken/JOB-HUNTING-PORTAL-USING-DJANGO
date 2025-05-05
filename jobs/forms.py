from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Job, JobApplication, Country, Province, City, Barangay
import os
import time

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                user_type=self.cleaned_data['user_type']
            )
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user_type', 'phone_number', 'address', 'bio', 'profile_picture', 'theme']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'profile_picture': 'Profile Picture (JPG, PNG)',
            'theme': 'Theme Preference'
        }
        help_texts = {
            'profile_picture': 'Upload a profile picture in JPG or PNG format (max 2MB)',
            'theme': 'Choose your preferred theme for the website'
        }

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size (2MB max)
            if profile_picture.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Profile picture size should not exceed 2MB.')
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(profile_picture.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError('Please upload a valid image file (JPG, PNG).')
            
            # Rename file to avoid conflicts
            filename = f"profile_{self.instance.user.username}_{int(time.time())}{ext}"
            profile_picture.name = filename
            
        return profile_picture

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('title', 'country', 'province', 'city', 'barangay', 'job_type', 'salary_range', 'description', 'requirements', 'deadline')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['province'].queryset = Province.objects.none()
        self.fields['city'].queryset = City.objects.none()
        self.fields['barangay'].queryset = Barangay.objects.none()

        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['province'].queryset = Province.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['province'].queryset = self.instance.country.provinces.order_by('name')

        if 'province' in self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['city'].queryset = City.objects.filter(province_id=province_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['city'].queryset = self.instance.province.cities.order_by('name')

        if 'city' in self.data:
            try:
                city_id = int(self.data.get('city'))
                self.fields['barangay'].queryset = Barangay.objects.filter(city_id=city_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['barangay'].queryset = self.instance.city.barangays.order_by('name')

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('cover_letter', 'resume')
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'cover_letter': 'Cover Letter',
            'resume': 'Resume (PDF, DOC, DOCX)'
        }
        help_texts = {
            'resume': 'Upload your resume in PDF or Word format (max 5MB)'
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            # Check file size (5MB limit)
            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB')
            
            # Check file type
            valid_extensions = ['.pdf', '.doc', '.docx']
            ext = os.path.splitext(resume.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError('Please upload a PDF or Word document')
            
            # Rename file to avoid conflicts
            filename = f"resume_{int(time.time())}{ext}"
            resume.name = filename
            
        return resume 