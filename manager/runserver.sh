#!/bin/bash
echo "Making migrations"
while ! python manage.py makemigrations
do
  echo Sleeping 1 second waiting for database ${DB_HOST} ${DB_PORT}
  sleep 1
done
echo "Conected to ${DB_HOST} ${DB_PORT}"

echo "Applying migrations"
python manage.py migrate

echo "Creating default users"
python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} --cmduserpass ${CMD_USER_PASS}
echo "Applying fixtures"
python manage.py loaddata ui_framework/fixtures/initial_data.json

echo "Starting server"
daphne -b 0.0.0.0 -p 8000 manager.asgi:application
