# LOVE Manager

This repository contains the code of the Django Channels project that acts as middleware for the LOVE-frontend

## Basic local usage

Run the producer as in https://github.com/lsst-ts/LOVE-backend/blob/master/README.md

Run redis from the `LOVE-integration-tools/deploy/dev$`

```docker-compose up redis```

Move to the telemetry-manager folder and load a virtualenv

```
python3 -m venv virtualenv
source virtualenv/bin/activate
```

and open the manager:

```
python3 manage.py runserver
```


Open  https://www.websocket.org/echo.html in a browser and connect to this address: 

```
ws://localhost:8000/ws/subscription/
```

And send this message:
`{"option": "subscribe", "data": "avoidanceRegions"}`

In the log you should see something like:

```
RECEIVED: {"data": "Successfully subscribed to \"avoidanceRegions\""}


RECEIVED: {"data": {"avoidanceRegions": 1, "scale": 0.4713086485862732, "timestamp": 0.8468274284829842, "zero": 0.17323127388954163}}


...
```