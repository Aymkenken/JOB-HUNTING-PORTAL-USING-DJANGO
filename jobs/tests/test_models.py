from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from ..models import (
    Country, Province, City, Barangay,
    UserProfile, Location, Job, JobApplication,
    Notification
)

class CountryModelTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name="Philippines",
            code="PH"
        )

    def test_country_creation(self):
        self.assertEqual(self.country.name, "Philippines")
        self.assertEqual(self.country.code, "PH")

    def test_country_code_validation(self):
        with self.assertRaises(ValidationError):
            Country.objects.create(
                name="Invalid Country",
                code="123"  # Invalid code format
            )

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

    def test_profile_creation(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertIn(self.profile.user_type, ['job_seeker', 'employer'])

    def test_phone_number_validation(self):
        self.profile.phone_number = "1234567890"
        self.profile.save()
        self.assertEqual(self.profile.phone_number, "+1234567890")

class JobModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="employer",
            email="employer@example.com",
            password="testpass123"
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.user_type = 'employer'
        self.profile.save()

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

    def test_job_creation(self):
        job = Job.objects.create(
            title="Software Developer",
            company=self.user,
            job_type="full_time",
            location=self.location,
            description="Job description",
            requirements="Job requirements",
            salary_range="₱30,000 - ₱40,000",
            deadline=timezone.now().date() + timedelta(days=30)
        )
        self.assertEqual(job.title, "Software Developer")
        self.assertEqual(job.company, self.user)
        self.assertEqual(job.views_count, 0)
        self.assertEqual(job.applications_count, 0)

    def test_job_deadline_validation(self):
        with self.assertRaises(ValidationError):
            Job.objects.create(
                title="Invalid Job",
                company=self.user,
                job_type="full_time",
                location=self.location,
                description="Job description",
                requirements="Job requirements",
                salary_range="₱30,000 - ₱40,000",
                deadline=timezone.now().date() - timedelta(days=1)
            )

class JobApplicationModelTest(TestCase):
    def setUp(self):
        # Create employer
        self.employer = User.objects.create_user(
            username="employer",
            email="employer@example.com",
            password="testpass123"
        )
        self.employer_profile = UserProfile.objects.get(user=self.employer)
        self.employer_profile.user_type = 'employer'
        self.employer_profile.save()

        # Create job seeker
        self.applicant = User.objects.create_user(
            username="applicant",
            email="applicant@example.com",
            password="testpass123"
        )
        self.applicant_profile = UserProfile.objects.get(user=self.applicant)
        self.applicant_profile.user_type = 'job_seeker'
        self.applicant_profile.save()

        # Create job
        self.job = Job.objects.create(
            title="Software Developer",
            company=self.employer,
            job_type="full_time",
            description="Job description",
            requirements="Job requirements",
            salary_range="₱30,000 - ₱40,000",
            deadline=timezone.now().date() + timedelta(days=30)
        )

    def test_application_creation(self):
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            cover_letter="I am interested in this position",
            resume="resume.pdf"
        )
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.applicant, self.applicant)
        self.assertEqual(application.status, "pending")
        self.assertEqual(self.job.applications_count, 1)

    def test_duplicate_application(self):
        JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            cover_letter="First application",
            resume="resume1.pdf"
        )
        with self.assertRaises(ValidationError):
            JobApplication.objects.create(
                job=self.job,
                applicant=self.applicant,
                cover_letter="Second application",
                resume="resume2.pdf"
            )

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type="new_application",
            title="New Application",
            message="You have received a new application"
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, "new_application")
        self.assertFalse(notification.is_read)

    def test_notification_expiration(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type="new_application",
            title="New Application",
            message="You have received a new application",
            expires_at=timezone.now() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            notification.full_clean() 