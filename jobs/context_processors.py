from .models import UserProfile

def theme_context(request):
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            theme = user_profile.theme
        except UserProfile.DoesNotExist:
            theme = 'light'
    else:
        theme = 'light'
    
    return {
        'theme': theme,
        'is_dark_theme': theme == 'dark'
    } 