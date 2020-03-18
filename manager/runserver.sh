#!/bin/bash
echo "\nMaking migrations"
while ! python manage.py makemigrations
do
  echo "Sleeping 1 second waiting for database ${DB_HOST} ${DB_PORT}"
  sleep 1
done
echo "\nConected to ${DB_HOST} ${DB_PORT}"

echo "\nApplying migrations"
python manage.py migrate

echo "\nCreating default users"
python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} --cmduserpass ${CMD_USER_PASS}
echo "\nApplying fixtures"
mkdir -p media/thumbnails
cp -u ui_framework/fixtures/thumbnails/* media/thumbnails
python manage.py loaddata ui_framework/fixtures/initial_data.json

echo "\nStarting server"
daphne -b 0.0.0.0 -p 8000 manager.asgi:application
