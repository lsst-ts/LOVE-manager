#!/bin/bash
echo -e "\nMaking migrations"
while ! python manage.py makemigrations
do
  echo -e "Sleeping 1 second waiting for database ${DB_HOST} ${DB_PORT}"
  sleep 1
done
echo -e "\nConected to ${DB_HOST} ${DB_PORT}"

echo -e "\nApplying migrations"
python manage.py migrate

echo -e "\nCreating default users"
python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} --cmduserpass ${CMD_USER_PASS}
echo -e "\nApplying fixtures"
mkdir -p media/thumbnails
cp -u ui_framework/fixtures/thumbnails/* media/thumbnails
cp -u api/fixtures/configs/* media/configs

python manage.py loaddata ui_framework/fixtures/initial_data.json
python manage.py loaddata api/fixtures/initial_data.json

echo -e "\nStarting server"
daphne -b 0.0.0.0 -p 8000 manager.asgi:application
