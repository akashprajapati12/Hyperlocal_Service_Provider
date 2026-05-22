from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        import sys
        if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
            try:
                from django.core.management import call_command
                call_command('migrate', interactive=False)
            except Exception:
                pass
