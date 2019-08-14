#!/bin/bash

python manage.py makemigrations
python manage.py migrate

python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} --cmduserpass ${CMD_USER_PASS}
python manage.py runserver 0.0.0.0:8000
