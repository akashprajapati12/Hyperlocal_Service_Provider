"""
WSGI config for Hyperlocal_Service_Provider project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hyperlocal_Service_Provider.settings')

django.setup()

# Auto-migrate SQLite on Vercel startup (ephemeral /tmp db)
if os.environ.get('VERCEL') and not os.environ.get('DATABASE_URL'):
    try:
        from django.core.management import call_command
        print("Vercel environment detected with SQLite. Running migrations on startup...")
        call_command('migrate', interactive=False, verbosity=1)
    except Exception as e:
        print(f"Error running auto-migrations on Vercel startup: {e}")

application = get_wsgi_application()

app = application
