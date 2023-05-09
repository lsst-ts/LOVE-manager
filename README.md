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
- `AUTHLIST_USER_PASS`: password for the default `authlist` user, which has permissions to manage the authlist authorization requests.
- `SECRET_KEY`: overrides Django's SECRET_KEY, if not defined the default value (public in this repo) will be used.
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
- `COMMANDER_HOSTNAME`: defines the hostname of the LOVE-commander server.
- `COMMANDER_PORT`: defines the port of the LOVE-commander server.
- `LOVE_PRODUCER_LEGACY`: defines wether or not ussing the legacy LOVE-producer version. If the variable is defined, then the CSC Client won't be used and the legacy version will.
- `OLE_API_HOSTNAME`: defines the hostname of the OLE API server.
- `JIRA_API_HOSTNAME`: defines the hostname of the JIRA API server.
- `JIRA_PROJECT_ID`: defines the JIRA project ID to use.
- `JIRA_API_TOKEN`: defines the JIRA API token to use. This value is the `<user>:<password>` encoded as base64.
- `AUTH_LDAP_1_SERVER_URI`: defines the location of the LDAP authentication server, replica n°1. No LDAP server is used if this variable or its equivalents is empty
- `AUTH_LDAP_2_SERVER_URI`: defines the location of the LDAP authentication server, replica n°2. No LDAP server is used if this variable or its equivalents is empty
- `AUTH_LDAP_3_SERVER_URI`: defines the location of the LDAP authentication server, replica n°3. No LDAP server is used if this variable or its equivalents is empty
- `AUTH_LDAP_BIND_PASSWORD`: defines the password to use to bind to the LDAP server. This is the password of the provided user for LDAP actions: svc_love.
- `LOVE_SITE`: defines the site name of the LOVE system. This value is used to identify the LOVE system in the LOVE-manager.
- `REMOTE_STORAGE`: defines if remote storage is used. If this variable is defined, then the LOVE-manager will connect to the LFA to upload files. If not defined, then the LOVE-manager will store the files locally.

# Local load for development

We provide docker images and a docker-compose file in order to load the LOVE-manager with a Postgres database locally, for development purposes, such as run tests and build documentation.

This docker-compose does not copy the code into the image, but instead it mounts the repository inside the image, this way you can edit the code from outside the docker container with no need to rebuild or restart.

## Load and get into the docker image

Follow these instructions to run the application in a docker container and get into it:

```
cd docker/
docker-compose up -d --build
docker-compose exec manager bash
cd /usr/src/love/manager/
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

### Linting & Formatting
In order to maintaing code linting and formatting we use `pre-commit` that runs **Flake8** (https://flake8.pycqa.org/) and **Black** (https://github.com/psf/black) using Git Hooks. To enable this you have to:

1. Install `pre-commit` in your local development environment:
```
pip install pre-commit
```

2. Set up the git hook scripts running:
```
pre-commit install
```

3. Start developing! Linter and Formatter will be executed on every commit you make