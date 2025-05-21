from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
import os
from datetime import timedelta
import uuid
from django.conf import settings
import re

def validate_file_size(value):
    if not value:
        return
    try:
        # For new uploads
        if hasattr(value, 'size'):
            filesize = value.size
        # For existing files
        elif hasattr(value, 'path'):
            filesize = os.path.getsize(value.path)
        else:
            return
            
        if filesize > 2 * 1024 * 1024:  # 2MB
            raise ValidationError("The maximum file size that can be uploaded is 2MB")
    except (FileNotFoundError, OSError, AttributeError):
        # If the file doesn't exist yet or can't be accessed,
        # we'll skip the size validation. The file will be validated again when saved.
        pass

def validate_resume_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported file extension. Please upload PDF or Word documents only.')

class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True, validators=[
        RegexValidator(
            regex='^[A-Z]{2}$',
            message='Country code must be 2 uppercase letters',
            code='invalid_country_code'
        )
    ])

    class Meta:
        verbose_name_plural = "Countries"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
        ]
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.code:
            self.code = self.code.upper()

class Province(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='provinces')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['country', 'name']),
            models.Index(fields=['code']),
        ]
        ordering = ['country', 'name']
        unique_together = ['country', 'name']

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name_plural = "Cities"
        indexes = [
            models.Index(fields=['province', 'name']),
            models.Index(fields=['code']),
        ]
        ordering = ['province', 'name']
        unique_together = ['province', 'name']

    def __str__(self):
        return f"{self.name}, {self.province.name}"

class Barangay(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='barangays')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = "Barangays"
        indexes = [
            models.Index(fields=['city', 'name']),
            models.Index(fields=['code']),
        ]
        ordering = ['city', 'name']
        unique_together = ['city', 'name']

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('jobseeker', 'Job Seeker'),
        ('employer', 'Employer'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='jobseeker')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    
    # Social Media Links
    linkedin = models.URLField(max_length=200, null=True, blank=True)
    github = models.URLField(max_length=200, null=True, blank=True)
    
    # Job Seeker Specific Fields
    skills = models.TextField(null=True, blank=True, help_text='Comma-separated list of skills')
    
    # Employer Specific Fields
    company_name = models.CharField(max_length=100, null=True, blank=True)
    company_website = models.URLField(max_length=200, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_skills_list(self):
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',')]
        return []
    
    def save(self, *args, **kwargs):
        # Delete old profile picture if it exists and a new one is being uploaded
        if self.pk:
            try:
                old_profile = UserProfile.objects.get(pk=self.pk)
                if old_profile.profile_picture and self.profile_picture and old_profile.profile_picture != self.profile_picture:
                    if os.path.isfile(old_profile.profile_picture.path):
                        os.remove(old_profile.profile_picture.path)
            except UserProfile.DoesNotExist:
                pass
        super().save(*args, **kwargs)

class Location(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['country', 'province', 'city', 'barangay']
        indexes = [
            models.Index(fields=['country', 'province', 'city', 'barangay']),
        ]

    def __str__(self):
        location_parts = []
        if self.barangay:
            location_parts.append(self.barangay.name)
        if self.city:
            location_parts.append(self.city.name)
        if self.province:
            location_parts.append(self.province.name)
        if self.country:
            location_parts.append(self.country.name)
        return ", ".join(location_parts) if location_parts else "No location specified"

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]

    title = models.CharField(max_length=200)
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    company_name = models.CharField(max_length=200, null=True, blank=True)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    description = models.TextField()
    requirements = models.TextField()
    salary_range = models.CharField(max_length=100)
    posted_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['company']),
            models.Index(fields=['company_name']),
            models.Index(fields=['job_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['deadline']),
            models.Index(fields=['views_count']),
            models.Index(fields=['applications_count']),
        ]

    def __str__(self):
        return self.title

    def get_location_display(self):
        if self.location:
            return str(self.location)
        return "No location specified"

    def clean(self):
        super().clean()
        
        # Validate deadline
        if self.deadline and self.deadline < timezone.now().date():
            raise ValidationError({'deadline': 'Deadline cannot be in the past'})
        
        # Validate salary range format
        if self.salary_range:
            try:
                # Extract numbers from the salary range
                numbers = re.findall(r'\d+', self.salary_range)
                
                if len(numbers) != 2:
                    raise ValidationError({'salary_range': 'Please enter valid minimum and maximum salary values'})
                
                # Convert to integers and validate
                min_salary = int(numbers[0].replace(',', ''))
                max_salary = int(numbers[1].replace(',', ''))
                
                if min_salary < 0 or max_salary < 0:
                    raise ValidationError({'salary_range': 'Salary amounts cannot be negative'})
                
                if min_salary >= max_salary:
                    raise ValidationError({'salary_range': 'Minimum salary must be less than maximum salary'})
                
                if min_salary > 1000000000 or max_salary > 1000000000:
                    raise ValidationError({'salary_range': 'Salary amounts are too high'})
                    
            except (ValueError, TypeError):
                raise ValidationError({'salary_range': 'Please enter valid salary values'})
        
        # Validate job type
        if self.job_type not in [choice[0] for choice in self.JOB_TYPE_CHOICES]:
            raise ValidationError({'job_type': 'Please select a valid job type'})
        
        # Validate title length
        if len(self.title) < 5:
            raise ValidationError({'title': 'Title must be at least 5 characters long'})
        
        # Validate description and requirements
        if len(self.description) < 50:
            raise ValidationError({'description': 'Description must be at least 50 characters long'})
        
        if len(self.requirements) < 20:
            raise ValidationError({'requirements': 'Requirements must be at least 20 characters long'})

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_applications(self):
        self.applications_count += 1
        self.save(update_fields=['applications_count'])

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField()
    resume = models.FileField(
        upload_to='resumes/',
        validators=[
            validate_resume_extension,
            validate_file_size
        ]
    )
    additional_info = models.TextField(null=True, blank=True, help_text='Any additional information you would like to share with the employer')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'applicant')
        indexes = [
            models.Index(fields=['job', 'applicant']),
            models.Index(fields=['status']),
            models.Index(fields=['application_date']),
            models.Index(fields=['last_updated']),
        ]
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"

    def save(self, *args, **kwargs):
        if self.pk is None:  # New application
            self.job.increment_applications()
        super().save(*args, **kwargs)

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_application', 'New Application'),
        ('application_status', 'Application Status Update'),
        ('job_expiring', 'Job Expiring Soon'),
        ('new_message', 'New Message'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.user.username}"

    def clean(self):
        if self.expires_at and self.expires_at < timezone.now():
            raise ValidationError({'expires_at': 'Expiration date cannot be in the past'})

class EmailVerificationToken(models.Model):
    TOKEN_TYPES = (
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user']),
            models.Index(fields=['token_type']),
            models.Index(fields=['expires_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=1)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()

    def mark_as_used(self):
        self.is_used = True
        self.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        try:
            # Get the user type from the form data
            user_type = getattr(instance, '_user_type', None)
            if not user_type:
                # If no user type is set, don't create the profile here
                # Let the form handle it
                return
            # Create the profile with the correct user type
            UserProfile.objects.create(user=instance, user_type=user_type)
        except Exception as e:
            # If there's any error, don't create a default profile
            # Let the form handle it
            pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # If profile doesn't exist, don't create it here
        # Let the form handle it
        pass 