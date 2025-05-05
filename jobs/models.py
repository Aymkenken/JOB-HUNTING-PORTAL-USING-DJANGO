from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True)

    def __str__(self):
        return self.name

class Province(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='provinces')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name}, {self.province.name}"

class Barangay(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='barangays')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('job_seeker', 'Job Seeker'),
        ('employer', 'Employer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]

    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    salary_range = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    posted_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.company.username}"

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
    resume = models.FileField(upload_to='resumes/')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"

    class Meta:
        unique_together = ('job', 'applicant') 