from .models import UserProfile

def theme_context(request):
    if request.user.is_authenticated:
        try:
            theme = request.user.userprofile.theme
        except:
            theme = 'light'
    else:
        theme = 'light'
    
    return {
        'theme': theme,
        'is_dark_theme': theme == 'dark'
    } 