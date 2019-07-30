Introduction
===============

The LOVE-manager is part of the LSST Operation and Visualization Environment (L.O.V.E.) project.
It is written in Python using both Django Rest Framework (DRF) and Django Channels.

The LOVE-manager is an intermediary between the LOVE-producer and the LOVE-frontend.
It handles websockets connections and redirect messages to subscribers following the Django Channels consumers and groups workflow.
It also provides an API for token-based authentication and authorization.

Currently the application has 2 Django apps:

* **API:** This app contains the models and API endpoints for authentication. For more details please refer to the ApiDoc section
* **Subscription:** This app contains the consumers that handle the websocket communication. Users need to have an authentication token to establish a connection.
