from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from ..models import (
    Country, Province, City, Barangay,
    UserProfile, Location, Job, JobApplication
)

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('home')

    def test_home_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

class JobListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('job_list')
        
        # Create test user
        self.user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.user_type = 'employer'
        self.profile.save()

        # Create test location
        self.country = Country.objects.create(name="Philippines", code="PH")
        self.province = Province.objects.create(
            country=self.country,
            name="Surigao del Norte",
            code="SUN"
        )
        self.city = City.objects.create(
            province=self.province,
            name="Surigao City",
            code="SUR"
        )
        self.barangay = Barangay.objects.create(
            city=self.city,
            name="Taft",
            code="TAFT"
        )
        self.location = Location.objects.create(
            country=self.country,
            province=self.province,
            city=self.city,
            barangay=self.barangay
        )

        # Create test job
        self.job = Job.objects.create(
            title="Software Developer",
            company=self.user,
            job_type="full_time",
            location=self.location,
            description="Job description",
            requirements="Job requirements",
            salary_range="₱30,000 - ₱40,000",
            deadline=timezone.now().date() + timedelta(days=30)
        )

    def test_job_list_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_list.html')
        self.assertContains(response, self.job.title)

    def test_job_list_search(self):
        response = self.client.get(self.url, {'query': 'software'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.job.title)

        response = self.client.get(self.url, {'query': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.job.title)

class JobDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.user_type = 'employer'
        self.profile.save()

        # Create test location
        self.country = Country.objects.create(name="Philippines", code="PH")
        self.province = Province.objects.create(
            country=self.country,
            name="Surigao del Norte",
            code="SUN"
        )
        self.city = City.objects.create(
            province=self.province,
            name="Surigao City",
            code="SUR"
        )
        self.barangay = Barangay.objects.create(
            city=self.city,
            name="Taft",
            code="TAFT"
        )
        self.location = Location.objects.create(
            country=self.country,
            province=self.province,
            city=self.city,
            barangay=self.barangay
        )

        # Create test job
        self.job = Job.objects.create(
            title="Software Developer",
            company=self.user,
            job_type="full_time",
            location=self.location,
            description="Job description",
            requirements="Job requirements",
            salary_range="₱30,000 - ₱40,000",
            deadline=timezone.now().date() + timedelta(days=30)
        )
        self.url = reverse('job_detail', args=[self.job.id])

    def test_job_detail_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_detail.html')
        self.assertContains(response, self.job.title)
        self.assertEqual(self.job.views_count, 1)

    def test_nonexistent_job(self):
        response = self.client.get(reverse('job_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

class JobApplicationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create employer
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123'
        )
        self.employer_profile = UserProfile.objects.get(user=self.employer)
        self.employer_profile.user_type = 'employer'
        self.employer_profile.save()

        # Create applicant
        self.applicant = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='testpass123'
        )
        self.applicant_profile = UserProfile.objects.get(user=self.applicant)
        self.applicant_profile.user_type = 'job_seeker'
        self.applicant_profile.save()

        # Create test location
        self.country = Country.objects.create(name="Philippines", code="PH")
        self.province = Province.objects.create(
            country=self.country,
            name="Surigao del Norte",
            code="SUN"
        )
        self.city = City.objects.create(
            province=self.province,
            name="Surigao City",
            code="SUR"
        )
        self.barangay = Barangay.objects.create(
            city=self.city,
            name="Taft",
            code="TAFT"
        )
        self.location = Location.objects.create(
            country=self.country,
            province=self.province,
            city=self.city,
            barangay=self.barangay
        )

        # Create test job
        self.job = Job.objects.create(
            title="Software Developer",
            company=self.employer,
            job_type="full_time",
            location=self.location,
            description="Job description",
            requirements="Job requirements",
            salary_range="₱30,000 - ₱40,000",
            deadline=timezone.now().date() + timedelta(days=30)
        )
        self.url = reverse('apply_job', args=[self.job.id])

    def test_apply_job_authenticated(self):
        self.client.login(username='applicant', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/apply_job.html')

    def test_apply_job_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_submit_application(self):
        self.client.login(username='applicant', password='testpass123')
        form_data = {
            'cover_letter': 'I am interested in this position',
            'resume': 'test.pdf'
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 302)  # Redirects after successful submission
        self.assertTrue(JobApplication.objects.filter(
            job=self.job,
            applicant=self.applicant
        ).exists())

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('dashboard')
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)

    def test_dashboard_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_dashboard_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('profile')
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)

    def test_profile_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_profile_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_update_profile(self):
        self.client.login(username='testuser', password='testpass123')
        form_data = {
            'phone_number': '1234567890',
            'address': '123 Test St',
            'bio': 'Test bio'
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 302)  # Redirects after successful update
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone_number, '+1234567890')
        self.assertEqual(self.profile.address, '123 Test St')
        self.assertEqual(self.profile.bio, 'Test bio') 