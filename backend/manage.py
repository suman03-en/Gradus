#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gradus.settings.local')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

    # Automatically create superuser in production after migrations
    try:
        if "migrate" in sys.argv:
            import django
            from django.conf import settings
            
            if not settings.DEBUG:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admin_username = os.environ.get("DJANGO_ADMIN")
                admin_password = os.environ.get("DJANGO_ADMIN_PASSWORD")
                
                if admin_username and admin_password:
                    if not User.objects.filter(username=admin_username).exists():
                        User.objects.create_superuser(
                            username=admin_username,
                            email=f"{admin_username}@gradus.com",
                            password=admin_password
                        )
                        print(f"Successfully created expected production superuser: {admin_username}")
    except Exception as e:
        print(f"Could not auto-create superuser: {e}")


if __name__ == '__main__':
    main()
