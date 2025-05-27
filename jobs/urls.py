from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .custom_http_decorators import get_csrf_token
from .api_views import UserProfileViewSet, JobViewSet, JobApplicationViewSet, LocationViewSet

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', JobApplicationViewSet, basename='application')
router.register(r'locations', LocationViewSet, basename='location')

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    
    # Existing URLs
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/jobseeker/', views.register_jobseeker, name='register_jobseeker'),
    path('register/employer/', views.register_employer, name='register_employer'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('profile/', views.profile, name='profile'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('post-job/', views.post_job, name='post_job'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:application_id>/manage/', views.manage_application, name='manage_application'),
    path('load-provinces/', views.load_provinces, name='load_provinces'),
    path('load-cities/', views.load_cities, name='load_cities'),
    path('load-barangays/', views.load_barangays, name='load_barangays'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('manage-locations/', views.manage_locations, name='manage_locations'),
    path('add-location/', views.add_location, name='add_location'),
    path('delete-location/<int:location_id>/', views.delete_location, name='delete_location'),
    path('csrf-token/', get_csrf_token, name='csrf_token'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('profile/update-type/', views.update_profile_type, name='update_profile_type'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    
    # Job Management URLs
    path('jobs/edit/<int:job_id>/', views.edit_job, name='edit_job'),
    path('jobs/applications/<int:job_id>/', views.job_applications, name='job_applications'),
    path('jobs/application/<int:application_id>/', views.view_application, name='view_application'),
    path('jobs/application/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('employer/applications/', views.employer_applications, name='employer_applications'),
    path('employer/analytics/', views.employer_analytics, name='employer_analytics'),
    path('employer/analytics/data/', views.employer_analytics_data, name='employer_analytics_data'),
] 