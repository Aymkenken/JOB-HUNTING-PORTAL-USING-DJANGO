INSTALLED_APPS = [
    # ... existing apps ...
    'channels',
]

ASGI_APPLICATION = 'jobportal.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
} 