import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "badris_foods.settings")
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="Admin@123"
    )
    print("Admin user created")
else:
    print("Admin already exists")