============
How it works
============

.. image:: ../assets/Manager_Details.svg


LOVE-manager parts
==================
The LOVE-manager is composed by different software components, as explained below.

API
---
Provides a REST API with endpoints to request and validate access tokens.
When a client (LOVE-frontend) tries to login it sends the users credentials (user and password) through an HTTP request to the API, which responds with the token (if the credentials are valid) or an error (if the credentials are invalid). The validation is done comparing searching the given user in the :code:`DB` and comparing the given password.

Consumers
---------
Once the client (LOVE-frontend) has an access token, it can establish a websocket connection with LOVE-manager's :code:`Channels Layer`. Each client (LOVE-frontend) instance is connected to a unique :code:`Consumer` instance, which handles the communication with that particular client.
Similarly, a :code:`Consumer` also handle the communication with a LOVE-producer instance.

Each :code:`consumer` communicates only with their corresponding clients. In order to receive messages from other clients, the consumer of a client must subscribe to a given group.
When a client sends a message to a group, it is forwarded to all the consumers subscribed to that group, which in turn send the message to their corresponding clients. All the message routing is done in the :code:`Channels Layer`.

Channel Layer
-------------
The :code:`Channels Layer` acts as the message handler, and is in charge of making sure every consumer receives the messages from the groups it has subscribed to.
When a client sends a message to its :code:`Consumer`, it is forwarded to the :code:`Channels Layer`. The :code:`Channels Layer` forwards the message to all the consumers subscribed to the group, and each consumer forwards the messages to its corresponding client.

DB
--
The :code:`DB` is used to model and store the users data (username, password and permissions). It is currently implemented in a simple :code:`.sqlite3` file, and is initialized with default users and groups.


Example
=======
In the figure above, we can see that :code:`Frontend 1` subscribes to telemetry :code:`tel1` while :code:`Frontend 2` subscribes to telemetries :code:`tel1` and :code:`tel2`.
When :code:`Producer` sends a value for :code:`tel1` to its consumer :code:`Consumer producer`, the latter forwards :code:`tel1` to the :code:`Channels Layer`, which forwards :code:`tel1` to :code:`Consumer 1` and :code:`Consumer 2`, each of which send :code:`tel1` to  :code:`Frontend 1` and :code:`Frontend 2` respectively.

Then, when :code:`Producer` sends a value for :code:`tel2` to :code:`Consumer producer`, the latter forwards :code:`tel2` to the :code:`Channels Layer`, which forwards :code:`tel2` to :code:`Consumer 2` only. Then :code:`Consumer 2` forwards the message to :code:`Frontend 2`.
In this case :code:`Frontend 1` (and :code:`Consumer 1`) never received :code:`tel2` because its not part of :code:`Consumer 1` subscriptions.


Code organization
==================

Currently the application is divided in the following modules and files:

* :code:`api`: This module contains the :code:`API` Django app, which defines the models and API endpoints for authentication. For more details please refer to the ApiDoc section
* :code:`subscription`: This module contains the Django app that defines the consumers that handle the websocket communication.
* :code:`manager`: This module contains basic Django configuration files, such as urls and channels routing, etc.
* :code:`manage.py`: This module is the main executable of the Django application, used mostly for development purposes, but also to execute some actions over the database, such as applying migrations, creating data, etc.
* :code:`pytest.ini`: This is the configuration file for the Pytest testing module.
* :code:`requierements.txt`: This file defines the python libraries required by the application.
* :code:`runserver.sh` and :code:`runserver-dev.sh`: These are simple scripts used to run the application inside the docker images.
