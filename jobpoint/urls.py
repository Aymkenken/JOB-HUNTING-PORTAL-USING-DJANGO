from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from jobs.routing import websocket_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('jobs.urls')),
    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='jobs/password_reset.html',
        email_template_name='jobs/password_reset_email.html',
        subject_template_name='jobs/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='jobs/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='jobs/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='jobs/password_reset_complete.html'
    ), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add WebSocket URL patterns
websocket_urlpatterns = websocket_urlpatterns 