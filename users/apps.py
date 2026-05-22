from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        # Do not run migrations automatically on AppConfig.ready().
        # Automatic migrations at import time are unsafe on serverless platforms like Vercel.
        return
