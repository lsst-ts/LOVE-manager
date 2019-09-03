============
How it works
============

Currently the application has 2 Django apps:

* **API:** This app contains the models and API endpoints for authentication. For more details please refer to the ApiDoc section
* **Subscription:** This app contains the consumers that handle the websocket communication. Users need to have an authentication token to establish a connection.
