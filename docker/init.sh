#!/bin/bash

source /home/saluser/.setup_sal_env.sh
PKG_DIR=$(python -c "import importlib.resources; print(importlib.resources.files('love.manager'))")

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
mkdir -p /usr/src/love-manager/media/thumbnails
cp -u ${PKG_DIR}/ui_framework/fixtures/thumbnails/* /usr/src/love-manager/media/thumbnails
if [ -d "${PKG_DIR}/ui_framework/fixtures/thumbnails/${love_site}" ]; then
  cp -u ${PKG_DIR}/ui_framework/fixtures/thumbnails/${love_site}/* /usr/src/love-manager/media/thumbnails
fi
mkdir -p /usr/src/love-manager/media/configs
cp -u ${PKG_DIR}/api/fixtures/configs/* /usr/src/love-manager/media/configs

if [ -z ${REMOTE_STORAGE} ]; then
  manage_love loaddata ${PKG_DIR}/api/fixtures/initial_data_${love_site}.json
else
  manage_love loaddata ${PKG_DIR}/api/fixtures/initial_data_remote_${love_site}.json
fi

manage_love loaddata ${PKG_DIR}/ui_framework/fixtures/initial_data_${love_site}.json
