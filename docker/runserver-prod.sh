#!/bin/bash

source /home/saluser/.setup_sal_env.sh
# cd $HOME/develop/python/love/manager

echo -e "\nMaking migrations"
while ! manage_love makemigrations
do
  echo -e "Sleeping 1 second waiting for database ${DB_HOST} ${DB_PORT}"
  sleep 1
done
echo -e "\nConected to ${DB_HOST} ${DB_PORT}"

echo -e "\nApplying migrations"
manage_love migrate

echo -e "\nCreating default users"
if [ "${LOVE_SITE}" == "summit" ]; then
  manage_love createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS} \
  --remotebaseuserpass ${REMOTE_BASE_USER_PASS} \
  --remotetucsonuserpass ${REMOTE_TUCSON_USER_PASS} \
  --remoteslacuserpass ${REMOTE_SLAC_USER_PASS}
else
  manage_love createusers --adminpass ${ADMIN_USER_PASS} --userpass ${USER_USER_PASS}
fi

if [ -z ${LOVE_SITE} ]; then
  love_site="summit"
else
  love_site=${LOVE_SITE}
fi
echo -e "\nSite: ${love_site}"

echo -e "\nApplying fixtures"
mkdir -p love-manager/media/thumbnails
cp -u ui_framework/fixtures/thumbnails/* love-manager/media/thumbnails
if [ -d "ui_framework/fixtures/thumbnails/${love_site}" ]; then
  cp -u ui_framework/fixtures/thumbnails/${love_site}/* love-manager/media/thumbnails
fi
mkdir -p love-manager/media/configs
cp -u api/fixtures/configs/* love-manager/media/configs

if [ -z ${REMOTE_STORAGE} ]; then
  manage_love loaddata api/fixtures/initial_data_${love_site}.json
else
  manage_love loaddata api/fixtures/initial_data_remote_${love_site}.json
fi

manage_love loaddata ui_framework/fixtures/initial_data_${love_site}.json

echo -e "\nStarting server"
if [ -z ${URL_SUBPATH} ]; then
  echo -e "\nStarting server without URL subpath"
  python -m uvicorn --host 0.0.0.0 --port 8000 manager.asgi:application
else
  echo -e "\nStarting server with URL subpath: ${URL_SUBPATH}"
  # python -m uvicorn --root-path ${URL_SUBPATH} --host 0.0.0.0 --port 8000 manager.asgi:application
  python -m uvicorn --host 0.0.0.0 --port 8000 love.manager.manager.asgi:application
fi