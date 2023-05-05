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
python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} --cmduserpass ${CMD_USER_PASS} --authlistuserpass ${AUTHLIST_USER_PASS}
if [ -z ${LOVE_SITE} ]; then
  love_site="summit"
else
  love_site=${LOVE_SITE}
fi
echo -e "\nSite: ${love_site}"
echo -e "\nApplying fixtures"
mkdir -p media/thumbnails
cp -u ui_framework/fixtures/thumbnails/* media/thumbnails
if [ -d "ui_framework/fixtures/thumbnails/${love_site}" ]; then
  cp -u ui_framework/fixtures/thumbnails/${love_site}/* media/thumbnails
fi
mkdir -p media/configs
cp -u api/fixtures/configs/* media/configs

python manage.py loaddata ui_framework/fixtures/initial_data_${love_site}.json

if [ -z ${REMOTE_STORAGE} ]; then
  python manage.py loaddata api/fixtures/initial_data.json
else
  python manage.py loaddata api/fixtures/initial_data_remote_${love_site}.json
fi

echo -e "\nStarting server"
daphne -b 0.0.0.0 -p 8000 manager.asgi:application
