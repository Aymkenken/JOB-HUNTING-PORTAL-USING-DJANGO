from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import UserProfile, Job, JobApplication, Country, Province, City, Barangay, Location
import os
import time
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from django.conf import settings
from datetime import datetime

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect(),
        error_messages={
            'required': 'Please select an account type.'
        }
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom help text for username
        self.fields['username'].help_text = (
            'Choose a unique username. Letters, numbers, and @/./+/-/_ characters are allowed.'
        )
        # Add custom widget attributes for username
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        # Add custom widget attributes for email
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address (optional)'
        })
        # Add custom widget attributes for password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
        # Add custom widget attributes for first_name and last_name
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
        
        # Ensure user_type is required and has no initial value
        self.fields['user_type'].required = True
        self.fields['user_type'].initial = None
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if not user_type:
            self.add_error('user_type', 'Please select an account type.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            # Store user_type for the signal
            user._user_type = self.cleaned_data['user_type']
            user.save()
            
            # Create the profile with the correct user type
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.create(
                    user=user,
                    user_type=self.cleaned_data['user_type']
                )
        
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    linkedin = forms.URLField(required=False)
    github = forms.URLField(required=False)
    skills = forms.CharField(required=False, help_text='Enter your skills separated by commas')
    company_name = forms.CharField(max_length=100, required=False)
    company_website = forms.URLField(required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'address',
            'bio', 'linkedin', 'github', 'skills', 'company_name',
            'company_website', 'profile_picture'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update User model fields
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            # Only update email if it's provided
            if self.cleaned_data.get('email'):
                user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile

class JobForm(forms.ModelForm):
    # Location fields
    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        required=True,
        help_text='Select the country where the job is located'
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all().order_by('name'),
        required=True,
        help_text='Select the province/state'
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.all().order_by('name'),
        required=True,
        help_text='Select the city'
    )
    barangay = forms.ModelChoiceField(
        queryset=Barangay.objects.all().order_by('name'),
        required=True,
        help_text='Select the barangay/district'
    )

    # Job details
    title = forms.CharField(
        max_length=200,
        required=True,
        help_text='Enter a clear and descriptive job title',
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Software Developer'})
    )
    company_name = forms.CharField(
        max_length=200,
        required=True,
        help_text='Enter your company name',
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Your Company Name'})
    )
    job_type = forms.ChoiceField(
        choices=Job.JOB_TYPE_CHOICES,
        required=True,
        help_text='Select the type of employment'
    )

    # Contact Information
    contact_email = forms.EmailField(
        required=True,
        help_text='Enter the contact email for job inquiries',
        widget=forms.EmailInput(attrs={'placeholder': 'e.g., contact@company.com'})
    )
    contact_number = forms.CharField(
        max_length=20,
        required=True,
        help_text='Enter the contact number for job inquiries',
        widget=forms.TextInput(attrs={'placeholder': 'e.g., +63 912 345 6789'})
    )

    # Salary fields
    CURRENCY_CHOICES = [
        ('₱', 'Philippine Peso (₱)'),
        ('$', 'US Dollar ($)'),
        ('€', 'Euro (€)'),
        ('£', 'British Pound (£)'),
        ('¥', 'Japanese Yen (¥)'),
        ('₩', 'Korean Won (₩)'),
        ('₹', 'Indian Rupee (₹)'),
        ('A$', 'Australian Dollar (A$)'),
        ('C$', 'Canadian Dollar (C$)'),
    ]

    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        required=True,
        initial='₱',
        help_text='Select the currency for the salary'
    )
    min_salary = forms.IntegerField(
        required=True,
        min_value=0,
        help_text='Enter the minimum salary amount',
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g., 15000',
            'class': 'form-control',
            'min': '0',
            'step': '1000'
        })
    )
    max_salary = forms.IntegerField(
        required=True,
        min_value=0,
        help_text='Enter the maximum salary amount',
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g., 20000',
            'class': 'form-control',
            'min': '0',
            'step': '1000'
        })
    )

    # Work schedule fields
    DAYS_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    work_days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select the working days'
    )

    TIME_CHOICES = [
        ('06:00', '6:00 AM'),
        ('07:00', '7:00 AM'),
        ('08:00', '8:00 AM'),
        ('09:00', '9:00 AM'),
        ('10:00', '10:00 AM'),
        ('11:00', '11:00 AM'),
        ('12:00', '12:00 PM'),
        ('13:00', '1:00 PM'),
        ('14:00', '2:00 PM'),
        ('15:00', '3:00 PM'),
        ('16:00', '4:00 PM'),
        ('17:00', '5:00 PM'),
        ('18:00', '6:00 PM'),
        ('19:00', '7:00 PM'),
        ('20:00', '8:00 PM'),
        ('21:00', '9:00 PM'),
        ('22:00', '10:00 PM'),
    ]

    work_start_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        required=True,
        help_text='Select the work start time'
    )
    work_end_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        required=True,
        help_text='Select the work end time'
    )

    description = forms.CharField(
        required=True,
        help_text='Provide a detailed description of the job responsibilities and duties',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the role and responsibilities in detail'})
    )
    requirements = forms.CharField(
        required=True,
        help_text='List the required qualifications and experience',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'List the required qualifications and experience'})
    )
    deadline = forms.DateField(
        required=True,
        help_text='Set the application deadline',
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()})
    )

    class Meta:
        model = Job
        fields = ('title', 'company_name', 'job_type', 'description', 'requirements', 'currency', 'min_salary', 'max_salary', 
                 'work_days', 'work_start_time', 'work_end_time', 'deadline', 'country', 'province', 'city', 'barangay',
                 'contact_email', 'contact_number')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up initial querysets for location fields
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['province'].queryset = Province.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'province' in self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['city'].queryset = City.objects.filter(province_id=province_id).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'city' in self.data:
            try:
                city_id = int(self.data.get('city'))
                self.fields['barangay'].queryset = Barangay.objects.filter(city_id=city_id).order_by('name')
            except (ValueError, TypeError):
                pass

        # Set initial values for Philippines and Surigao
        philippines = Country.objects.filter(name='Philippines').first()
        if philippines:
            self.fields['country'].initial = philippines.id
            self.fields['province'].queryset = Province.objects.filter(country=philippines).order_by('name')
            
            surigao_del_norte = Province.objects.filter(name='Surigao del Norte').first()
            if surigao_del_norte:
                self.fields['province'].initial = surigao_del_norte.id
                self.fields['city'].queryset = City.objects.filter(province=surigao_del_norte).order_by('name')
                
                surigao_city = City.objects.filter(name='Surigao City').first()
                if surigao_city:
                    self.fields['city'].initial = surigao_city.id
                    self.fields['barangay'].queryset = Barangay.objects.filter(city=surigao_city).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        min_salary = cleaned_data.get('min_salary')
        max_salary = cleaned_data.get('max_salary')
        currency = cleaned_data.get('currency')
        work_start_time = cleaned_data.get('work_start_time')
        work_end_time = cleaned_data.get('work_end_time')
        work_days = cleaned_data.get('work_days')

        # Salary validation
        if min_salary is not None and max_salary is not None:
            try:
                # Convert to integers, handling both string and integer inputs
                min_salary = int(str(min_salary).replace(',', ''))
                max_salary = int(str(max_salary).replace(',', ''))

                # Basic validation
                if min_salary < 0 or max_salary < 0:
                    self.add_error('min_salary', 'Salary amounts cannot be negative')
                    return cleaned_data

                if min_salary >= max_salary:
                    self.add_error('min_salary', 'Minimum salary must be less than maximum salary')
                    return cleaned_data

                if min_salary > 1000000000 or max_salary > 1000000000:
                    self.add_error('min_salary', 'Salary amounts are too high')
                    return cleaned_data

                # Format salary range
                if currency:
                    min_salary_formatted = f"{min_salary:,}"
                    max_salary_formatted = f"{max_salary:,}"
                    cleaned_data['salary_range'] = f"{currency}{min_salary_formatted} - {currency}{max_salary_formatted}"

            except (ValueError, TypeError) as e:
                self.add_error('min_salary', 'Please enter valid salary amounts')
                return cleaned_data

        # Work schedule validation
        if work_start_time and work_end_time and work_start_time >= work_end_time:
            self.add_error('work_start_time', 'Work start time must be before work end time')

        if not work_days:
            self.add_error('work_days', 'Please select at least one working day')

        # Format work schedule
        if work_days and work_start_time and work_end_time:
            days_str = ', '.join([day.capitalize() for day in work_days])
            start_time = datetime.strptime(work_start_time, '%H:%M').strftime('%I:%M %p')
            end_time = datetime.strptime(work_end_time, '%H:%M').strftime('%I:%M %p')
            cleaned_data['work_schedule'] = f"{days_str}, {start_time} - {end_time}"

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Create or get location based on selected fields
        location, created = Location.objects.get_or_create(
            country=self.cleaned_data['country'],
            province=self.cleaned_data['province'],
            city=self.cleaned_data['city'],
            barangay=self.cleaned_data['barangay']
        )
        
        instance.location = location
        
        # Set salary_range from cleaned_data
        if 'salary_range' in self.cleaned_data:
            instance.salary_range = self.cleaned_data['salary_range']
        
        if commit:
            try:
                instance.full_clean()  # Validate the instance before saving
                instance.save()
            except ValidationError as e:
                # If validation fails, add the errors to the form
                for field, errors in e.message_dict.items():
                    if field not in self._errors:
                        self._errors[field] = self.error_class()
                    self._errors[field].extend(errors)
                raise
        
        return instance

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('cover_letter', 'resume', 'additional_info')
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
            'additional_info': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'cover_letter': 'Cover Letter',
            'resume': 'Resume (PDF, DOC, DOCX)',
            'additional_info': 'Additional Information'
        }
        help_texts = {
            'cover_letter': 'Explain why you are interested in this position and how your skills match the requirements.',
            'resume': 'Upload your resume in PDF or Word format (max 5MB).',
            'additional_info': 'Any additional information you would like to share with the employer.'
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            # Check file size (5MB limit)
            if resume.size > 5 * 1024 * 1024:
                raise ValidationError('Resume file size must be less than 5MB.')
            
            # Check file type
            ext = os.path.splitext(resume.name)[1].lower()
            if ext not in ['.pdf', '.doc', '.docx']:
                raise ValidationError('Only PDF and Word documents are allowed.')
        
        return resume

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ('country', 'province', 'city', 'barangay')

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get('country')
        province = cleaned_data.get('province')
        city = cleaned_data.get('city')
        barangay = cleaned_data.get('barangay')

        if province and province.country != country:
            raise ValidationError("Selected province does not belong to the selected country")

        if city and city.province != province:
            raise ValidationError("Selected city does not belong to the selected province")

        if barangay and barangay.city != city:
            raise ValidationError("Selected barangay does not belong to the selected city")

        return cleaned_data

class JobSearchForm(forms.Form):
    query = forms.CharField(required=False, max_length=100)
    job_type = forms.ChoiceField(required=False, choices=[('', 'All Types')] + list(Job.JOB_TYPE_CHOICES))
    location = forms.ModelChoiceField(required=False, queryset=Location.objects.all())
    sort_by = forms.ChoiceField(required=False, choices=[
        ('-posted_date', 'Newest First'),
        ('posted_date', 'Oldest First'),
        ('title', 'Title (A-Z)'),
        ('-title', 'Title (Z-A)'),
        ('salary_range', 'Salary (Low to High)'),
        ('-salary_range', 'Salary (High to Low)'),
        ('deadline', 'Deadline (Soonest)'),
        ('-deadline', 'Deadline (Latest)')
    ])

    def clean_query(self):
        query = self.cleaned_data.get('query')
        if query and len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters long")
        return query 

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError(_("No user found with this email address."))
        return email

class SetNewPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("The two password fields didn't match."))
        return password2

class EmailVerificationForm(forms.Form):
    token = forms.UUIDField(
        widget=forms.HiddenInput()
    )

    def clean_token(self):
        token = self.cleaned_data.get('token')
        if not token:
            raise ValidationError(_("Invalid verification token."))
        return token 

class DeleteProfileForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_delete = forms.BooleanField(required=True)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Incorrect password')
        return password

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('confirm_delete'):
            raise ValidationError('You must confirm that you want to delete your profile')
        return cleaned_data 

class JobSeekerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        help_text='Optional: Add your email for job notifications and account recovery',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email (optional)',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'autocomplete': 'family-name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a unique username',
            'autocomplete': 'username'
        })
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        
        # Password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password'
        })
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and can\'t be entirely numeric.'
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create the profile with jobseeker type
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.create(
                    user=user,
                    user_type='jobseeker'
                )
        
        return user

class EmployerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        help_text='Optional: Add your email for job posting notifications and account recovery',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email (optional)',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'autocomplete': 'family-name'
        })
    )
    company_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name',
            'autocomplete': 'organization'
        })
    )
    company_website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company website (optional)',
            'autocomplete': 'url'
        })
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Briefly describe your company (optional)',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a unique username',
            'autocomplete': 'username'
        })
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        
        # Password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password'
        })
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and can\'t be entirely numeric.'
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create the profile with employer type and company info
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.create(
                    user=user,
                    user_type='employer',
                    company_name=self.cleaned_data['company_name'],
                    company_website=self.cleaned_data.get('company_website', ''),
                    bio=self.cleaned_data.get('bio', '')
                )
        
        return user 