This repository contains the code of the Django Channels project that acts as middleware for the LOVE-frontend

See the documentation here: https://lsst-ts.github.io/LOVE-manager/html/index.html

# Use as part of the LOVE system
In order to use the LOVE-manager as part of the LOVE system we recommend to use the docker-compose and configuration files provided in the [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools) repo. Please follow the instructions there.

## Initialize Environment variables
In order to use the LOVE-manager, some environment variables must be defined before it is run.
All these variables are initialized with default variables defined in :code:`.env` files defined in the corresponding deployment environment defined in [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools). The are:

* `ADMIN_USER_PASS`: password for the default `admin` user, which has every permission.
* `USER_USER_PASS`: password for the default `user` user, which has readonly permissions and cannot execute commands.
* `CMD_USER_PASS`: password for the default `cmd` user, which has readonly permissions but can execute commands.
* `LOVE_MANAGER_REDIS_HOST`: the location of the redis host that implements the `Channels Layer`.
* `REDIS_PASS`: the password that the LOVE-manager needs tio use to connect with `redis`.
* `PROCESS_CONNECTION_PASS`: the password that the LOVE-producer will use to establish a websocket connection with the LOVE-manager.
* `AUTH_LDAP_SERVER_URI`: (deprecated) the location of the LDAP authentication server. No LDAP server is used if this variable is empty

# Local load for development
We provide a docker image and a docker-compose file in order to load the LOVE-manager locally for development purposes, i.e. run tests and build documentation.

This docker-compose does not copy the code into the image, but instead it mounts the repository inside the image, this way you can edit the code from outside the docker container with no need to rebuild or restart.

## Load and get into the docker image
Follow these instructions to run the application in a docker container and get into it:

```
docker-compose up -d
docker-exec manager bash
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
