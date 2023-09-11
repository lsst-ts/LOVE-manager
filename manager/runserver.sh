# !/bin/bash

# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


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

if [ -z ${REMOTE_STORAGE} ]; then
  python manage.py loaddata api/fixtures/initial_data_${love_site}.json
else
  python manage.py loaddata api/fixtures/initial_data_remote_${love_site}.json
fi

python manage.py loaddata ui_framework/fixtures/initial_data_${love_site}.json

echo -e "\nStarting server"
if [ -z ${URL_SUBPATH} ]; then
  daphne -b 0.0.0.0 -p 8000 manager.asgi:application
else
  daphne --root-path=${URL_SUBPATH} -b 0.0.0.0 -p 8000 manager.asgi:application
fi
