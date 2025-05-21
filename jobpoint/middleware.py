from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from jobs.models import UserProfile

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('home'),
            reverse('login'),
            reverse('register_choice'),
            reverse('register_jobseeker'),
            reverse('register_employer'),
        ]

        # Check if the current URL is in the public_urls list
        if request.path in public_urls:
            # If user is authenticated and has a profile, redirect to dashboard
            if request.user.is_authenticated:
                try:
                    # Check if user has a profile
                    if not hasattr(request.user, 'userprofile'):
                        # Create UserProfile if it doesn't exist
                        UserProfile.objects.create(
                            user=request.user,
                            user_type='jobseeker'  # Default to jobseeker
                        )
                        messages.info(request, 'Profile created successfully!')
                    
                    # Redirect to dashboard if user has a complete profile
                    return redirect('dashboard')
                except Exception as e:
                    messages.error(request, f'Error processing profile: {str(e)}')
                    return redirect('profile_settings')

        response = self.get_response(request)
        return response 