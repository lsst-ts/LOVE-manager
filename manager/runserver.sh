#!/bin/bash

python manage.py makemigrations
python manage.py migrate

python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} --cmduserpass ${CMD_USER_PASS}
daphne -b 0.0.0.0 -p 8000 manager.asgi:application
