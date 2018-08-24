SECRET_KEY = "it's-a-secret-to-everyone"

INSTALLED_APPS = [
    'channels',
    'channels_irc',
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
