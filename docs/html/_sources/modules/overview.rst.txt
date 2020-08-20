========
Overview
========

The LOVE-manager is part of the LSST Operation and Visualization Environment (L.O.V.E.) project.
It is written in Python using both Django Rest Framework (DRF) and Django Channels.

The LOVE-manager is an intermediary between the LOVE-producer and the LOVE-frontend.
It handles websockets connections and redirect messages to subscribers following the Django Channels consumers and groups workflow.
It also provides an API for token-based authentication and authorization.

.. image:: ../assets/Manager_Overview.svg

As shown in the figure, the LOVE-frontend sends access credentials to LOVE-manager, which replies with an access token. The LOVE-frontend then uses that token for every further communication.
The LOVE-frontend establishes a websocket connection with the LOVE-manager using the access token. Through that connection LOVE-frontend instances subscribe to different communication groups fer telemetries and events.
A communication group works as a pipe where every message sent to the group is forwarded to all the subscribers of the group. Therefore, once a client (or LOVE-frontend instance) has subscribed to a group the LOVE-manager will forward to the client any message that is sent to that group.

The LOVE-manager also receives all the data sent by the LOVE-producer, which includes telemetries, events and command acknowledgements. When the LOVE-manager receives a particular telemetry or event, it redirects the message to all the clients that have subscribed to that event.

When the LOVE-frontend sends a command to the LOVE-manager it is done through an HTTP request, the LOVE-Manager sends the command to the LOVE-Commander through another HTTP request. The LOVE-commander executes the command and sends the command's acknowledgement back to the LOVE-manager through the response of the original request.
Similarly, the LOVE-Manager sends the command acknowledgement to the LOVE-Frontend through the reponse of the original HTTP request.

The LOVE-Manager also provides an HTTP API to request data from SAL (SAL info). When this data is needed by a client, it is requested through HTTP to the LOVE-Manager, which in turns requests it from the LOVE-Commander.

Lastly, the LOVE-Manager receives observing logs messages from the LOVE-Frontend, which are sent through websockets to the LOVE-CSC. Once the LOVE-CSC writes the log message in SAL, an event is generated and it is received by the LOVE-Manager and LOVE-Frontend as any other event, through the LOVE-Producer.

For more details of how this communication works please check the :ref:`How it works` section.
