from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('post-job/', views.post_job, name='post_job'),
    path('applications/<int:application_id>/manage/', views.manage_application, name='manage_application'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    # Location AJAX endpoints
    path('ajax/load-provinces/', views.load_provinces, name='ajax_load_provinces'),
    path('ajax/load-cities/', views.load_cities, name='ajax_load_cities'),
    path('ajax/load-barangays/', views.load_barangays, name='ajax_load_barangays'),
] 