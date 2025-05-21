from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Job, JobApplication, Country, Province, City, Barangay

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_user_type')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_user_type(self, obj):
        try:
            return obj.userprofile.get_user_type_display()
        except:
            return "Not Set"
    get_user_type.short_description = 'User Type'

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'get_location', 'job_type', 'salary_range', 'deadline', 'is_active')
    list_filter = ('job_type', 'is_active', 'posted_date')
    search_fields = ('title', 'company__username', 'description')
    date_hierarchy = 'posted_date'
    readonly_fields = ('posted_date',)

    def get_location(self, obj):
        return str(obj.location) if obj.location else "-"
    get_location.short_description = 'Location'

class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'application_date', 'status', 'get_company')
    list_filter = ('status', 'application_date')
    search_fields = ('job__title', 'applicant__username', 'cover_letter')
    date_hierarchy = 'application_date'
    readonly_fields = ('application_date',)

    def get_company(self, obj):
        return obj.job.company
    get_company.short_description = 'Company'

# Register your models here
admin.site.register(Job, JobAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(Country)
admin.site.register(Province)
admin.site.register(City)
admin.site.register(Barangay) 