This repository contains the code of the Django Channels project that acts as middleware for the LOVE-frontend

See the documentation here: https://lsst-ts.github.io/LOVE-manager/html/index.html

# Use as part of the LOVE system

In order to use the LOVE-manager as part of the LOVE system we recommend to use the docker-compose and configuration files provided in the [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools) repo. Please follow the instructions there.

## Initialize Environment variables

In order to use the LOVE-manager, some environment variables must be defined before it is run.
All these variables are initialized with default variables defined in :code:`.env` files defined in the corresponding deployment environment defined in [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools). The are:

- `ADMIN_USER_PASS`: password for the default `admin` user, which has every permission.
- `USER_USER_PASS`: password for the default `user` user, which has readonly permissions and cannot execute commands.
- `CMD_USER_PASS`: password for the default `cmd` user, which has readonly permissions but can execute commands.
- `REDIS_HOST`: the location of the redis host that implements the `Channels Layer`.
- `REDIS_PASS`: the password that the LOVE-manager needs to use to connect with `redis`.
- `PROCESS_CONNECTION_PASS`: the password that the LOVE-producer will use to establish a websocket connection with the LOVE-manager.
- `DB_ENGINE`: describe which database engine should be used. If its value is `postgresql` Postgres will be used, otherwise it will use Sqlite3.
- `DB_NAME`: defines the name of the Database. Only used if `DB_ENGINE=postgresql`.
- `DB_USER`: defines the user of the Database. Only used if `DB_ENGINE=postgresql`.
- `DB_PASS`: defines the password of the Database. Only used if `DB_ENGINE=postgresql`.
- `DB_HOST`: defines the host of the Database. Only used if `DB_ENGINE=postgresql`.
- `DB_PORT`: defines the port of the Database. Only used if `DB_ENGINE=postgresql`.
- `NO_DEBUG`: defines wether or not the LOVE-.manager will be run using Django's debug mode. If the variable is defined, then Debug mode will be off.
- `SECRET_KEY`: overrides Django's SECRET_KEY, if not defined the default value (public in this repo) will be used.
- `AUTH_LDAP_SERVER_URI`: (deprecated) the location of the LDAP authentication server. No LDAP server is used if this variable is empty

# Local load for development

We provide a docker image and a docker-compose file in order to load the LOVE-manager with a Postgres database locally, for development purposes, such as run tests and build documentation.

This docker-compose does not copy the code into the image, but instead it mounts the repository inside the image, this way you can edit the code from outside the docker container with no need to rebuild or restart.

## Load and get into the docker image

Follow these instructions to run the application in a docker container and get into it:

```
docker-compose up -d
docker-compose exec manager bash
```

## Run tests

Once inside the container you will be in the `/usr/src/love/manager` folder, where you can run the tests as follows:

```
pytest
```

## Build documentation

Once inside the container you will be in the `/usr/src/love/manager` folder, where you can move out to the `docsrc` folder and build the documentation as follows:

```
cd ../docsrc
./create_docs.sh
```
