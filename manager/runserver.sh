#!/bin/bash

python manage.py makemigrations
python manage.py migrate

echo "from django.contrib.auth.models import User; User.objects.create_superuser('test', 'test@test.com', 'test') if (User.objects.filter(username='test').exists() == False) else None" | python manage.py shell

daphne -b 0.0.0.0 -p 8000 manager.asgi:application
