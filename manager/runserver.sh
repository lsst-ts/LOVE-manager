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
if [ "${LOVE_SITE}" == "summit" ]; then
  python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} \
  --remotebaseuserpass ${REMOTE_BASE_USER_PASS} \
  --remotetucsonuserpass ${REMOTE_TUCSON_USER_PASS} \
  --remoteslacuserpass ${REMOTE_SLAC_USER_PASS}
else
  python manage.py createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS}
fi

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

if [ -z ${REMOTE_STORAGE} ]; then
  python manage.py loaddata api/fixtures/initial_data_${love_site}.json
else
  python manage.py loaddata api/fixtures/initial_data_remote_${love_site}.json
fi

python manage.py loaddata ui_framework/fixtures/initial_data_${love_site}.json

echo -e "\nStarting server"
if [ -z ${URL_SUBPATH} ]; then
  python -m uvicorn --host 0.0.0.0 --port 8000 manager.asgi:application
else
  python -m uvicorn --root-path=${URL_SUBPATH} --host 0.0.0.0 --port 8000 manager.asgi:application
fi
