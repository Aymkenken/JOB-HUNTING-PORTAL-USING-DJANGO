import json
from django.http import JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from django.db import DatabaseError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_error(request, e)

    def handle_error(self, request, exception):
        if request.path.startswith('/api/'):
            return self.handle_api_error(exception)
        return self.handle_web_error(request, exception)

    def handle_api_error(self, exception):
        if isinstance(exception, ValidationError):
            return JsonResponse({
                'error': 'Validation Error',
                'details': exception.message_dict if hasattr(exception, 'message_dict') else str(exception)
            }, status=400)
        elif isinstance(exception, PermissionDenied):
            return JsonResponse({
                'error': 'Permission Denied',
                'details': str(exception)
            }, status=403)
        elif isinstance(exception, Http404):
            return JsonResponse({
                'error': 'Not Found',
                'details': str(exception)
            }, status=404)
        elif isinstance(exception, DatabaseError):
            logger.error(f"Database error: {str(exception)}")
            return JsonResponse({
                'error': 'Database Error',
                'details': 'An error occurred while processing your request'
            }, status=500)
        else:
            logger.error(f"Unexpected error: {str(exception)}")
            return JsonResponse({
                'error': 'Internal Server Error',
                'details': 'An unexpected error occurred'
            }, status=500)

    def handle_web_error(self, request, exception):
        if isinstance(exception, ValidationError):
            messages.error(request, str(exception))
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        elif isinstance(exception, PermissionDenied):
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('home')
        elif isinstance(exception, Http404):
            return render(request, '404.html', status=404)
        elif isinstance(exception, DatabaseError):
            logger.error(f"Database error: {str(exception)}")
            messages.error(request, 'An error occurred while processing your request.')
            return redirect('home')
        else:
            logger.error(f"Unexpected error: {str(exception)}")
            messages.error(request, 'An unexpected error occurred.')
            return redirect('home')

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        logger.info(f"Request: {request.method} {request.path}")
        
        # Process request
        response = self.get_response(request)
        
        # Log response
        logger.info(f"Response: {response.status_code}")
        
        return response

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        
        return response 