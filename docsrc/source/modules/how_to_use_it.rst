..
    This file is part of LOVE-manager.
..
    Copyright (c) 2023 Inria Chile.
..
    Developed for Inria Chile.
..
    This program is free software: you can redistribute it and/or modify it under 
    the terms of the GNU General Public License as published by the Free Software 
    Foundation, either version 3 of the License, or at your option any later version.
..
    This program is distributed in the hope that it will be useful,but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
    A PARTICULAR PURPOSE. See the GNU General Public License for more details.
..
    You should have received a copy of the GNU General Public License along with 
    this program. If not, see <http://www.gnu.org/licenses/>.


=============
How to use it
=============

Authentication
==============

LOVE-manager provides a token-based authentication mechanism.
Clients may request a token providing their credentials (username and password).

Token request, validation and logout operations are done via HTTP requests as follows:

Request token
-------------
Requests a new authorization token.
Returns token, user data and permissions

- Url: :code:`<IP>/manager/api/get-token/`
- HTTP Operation: POST
- Message JSON data:

.. code-block:: json

  {
    "username": "<username>",
    "password": "<password>",
  }

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "user": {
        "username": "<username>",
        "email": "<email>"
      },
      "token": "<token>",
      "permissions": {
        "execute_commands": "<true or false>"
      },
      "time_data": {
        "utc": "<server UTC time as a unix timestamp (seconds)>",
        "tai": "<server TAI time as a unix timestamp (seconds)>",
        "mjd": "<server time as Modified Julian Date>",
        "sidereal_summit": "<server sidereal time w/respect to the summit (hourangles)>",
        "sidereal_greenwich": "<server sidereal time w/respect to Greenwich (hourangles)>",
        "tai_to_utc": "<Difference between TAI and UTC times (seconds)>"
      },
      "config": {
        "alarms": {
          "minSeveritySound": "serious",
          "minSeverityNotification": "serious"
        },
        "camFeeds": {
          "generic": "/gencam",
          "allSky": "/gencam"
        }
      }
    }
  }

Validate token
--------------
Validates a given authorization token, passed through HTTP Headers.
Returns a confirmation of validity, user data, permissions, server_time and (optionally) the LOVE configuration file.
If the :code:`no_config` flag is added to the end of the URL, then the LOVE config files is not read and the corresponding value is returned as :code:`null`

- Url: :code:`<IP>/manager/api/validate-token/` or :code:`<IP>/manager/api/validate-token/no_config/`
- HTTP Operation: get
- Message HTTP Headers:

.. code-block:: json

  {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Token <token>"
  }

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "user": {
        "username": "<username>",
        "email": "<email>"
      },
      "token": "<token>",
      "permissions": {
        "execute_commands": "<true or false>"
      },
      "time_data": {
        "utc": "<server UTC time as a unix timestamp (seconds)>",
        "tai": "<server TAI time as a unix timestamp (seconds)>",
        "mjd": "<server time as Modified Julian Date>",
        "sidereal_summit": "<server sidereal time w/respect to the summit (hourangles)>",
        "sidereal_greenwich": "<server sidereal time w/respect to Greenwich (hourangles)>",
        "tai_to_utc": "<Difference between TAI and UTC times (seconds)>"
      },
      "config": {
        "alarms": {
          "minSeveritySound": "serious",
          "minSeverityNotification": "serious"
        },
        "camFeeds": {
          "generic": "/gencam",
          "allSky": "/gencam"
        }
      }
    }
  }

Swap token
--------------
Validates a given authorization token, passed through HTTP Headers.
Returns a confirmation of validity, user data, permissions, server_time and (optionally) the LOVE configuration file.
If the :code:`no_config` flag is added to the end of the URL, then the LOVE config files is not read and the corresponding value is returned as :code:`null`

- Url: :code:`<IP>/manager/api/swap-token/` or :code:`<IP>/manager/api/swap-token/no_config/`
- HTTP Operation: GET
- Message HTTP Headers:

.. code-block:: json

  {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Token <token>"
  }

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "user": {
        "username": "<username>",
        "email": "<email>"
      },
      "token": "<token>",
      "permissions": {
        "execute_commands": "<true or false>"
      },
      "time_data": {
        "utc": "<server UTC time as a unix timestamp (seconds)>",
        "tai": "<server TAI time as a unix timestamp (seconds)>",
        "mjd": "<server time as Modified Julian Date>",
        "sidereal_summit": "<server sidereal time w/respect to the summit (hourangles)>",
        "sidereal_greenwich": "<server sidereal time w/respect to Greenwich (hourangles)>",
        "tai_to_utc": "<Difference between TAI and UTC times (seconds)>"
      },
      "config": {
        "alarms": {
          "minSeveritySound": "serious",
          "minSeverityNotification": "serious"
        },
        "camFeeds": {
          "generic": "/gencam",
          "allSky": "/gencam"
        }
      }
    }
  }

Logout
------
Requests deletion of a given token, passed through HTTP Headers.
The token is deleted and a confirmation is replied.

- Url: :code:`<IP>/manager/api/logout/`
- HTTP Operation: DELETE
- Message HTTP Headers:

.. code-block:: json

  {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Token <token>"
  }

- Expected Response:

.. code-block:: json

  {
    "status": 204,
    "data": {
      "detail": "Logout successful, Token succesfully deleted",
    }
  }


Websockets Connection
=====================

Currently there are 2 ways to establish a websocket connection:

Authenticate with user token
----------------------------
This is the mechanism intended for end users. It requires them to have an authentication token.
In order to stablish the connection they must append the token to the websocket url as follows:

:code:`<IP>/manager/ws/subscription/?token=<my-token>`


Authenticate with password
----------------------------
This is the mechanism intended for other applications. It requires them to have the password token.
In order to stablish the connection they must append the password to the websocket url as follows:

:code:`<IP>/manager/ws/subscription/?password=<my-password>`


Websockets Messages
==============================

LOVE-manager Subscriptions scheme
---------------------------------

Group subscriptions are characterized by 4 variables:

* **category:** describe the category or type of stream.

    * ***telemetry:*** streams that transfer data from telemetry systems
    * ***event:*** streams that transfer data from events triggered asynchronously in the system
* **csc:** describes the type of the source CSC, e.g. :code:`ScriptQueue`
* **salindex:** describes the instance number (salindex) of a given the CSC, e.g. :code:`1`
* **stream:** describes the particular stream of the subscription.

The reasoning behind this scheme is that for a given CSC instance e.g. :code:`ScriptQueue 1` (salindex 1), there could be a number of telemetries, events or commands, each identified by a different :code:`stream`.

Messages types
--------------
The consumers accept/send the following types of messages:

Subscription messages
~~~~~~~~~~~~~~~~~~~~~
Specifying the variables necessary to subscribe a to a group in a JSON message, as follows:

.. code-block:: json

  {
    "option": "<subscribe/unsubscribe>",
    "category": "<event/telemetry/cmd>",
    "csc": "ScriptQueue",
    "salindex": 1,
    "stream": "stream1"
  }

Telemetry or Event messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specifying the data and the group where the message should be sent in a JSON message.
Consumer that receive these type of messages from their clients will forward them to the corresponding group. If consumers receive the message from the Channel Layer, then they will forward it to their clients.
They are defined as follows:

.. code-block:: json

  {
    "category": "event/telemetry",
    "data": [{
      "csc": "ScriptQueue",
      "salindex": 1,
      "data": {
          "stream1": {
            "<key1>": "<data1>",
            "<key2>": "<data2>",
          },
          "stream1": {
            "<key1>": "<data1>",
            "<key2>": "<data2>",
          },
      }
    }]
  }

Heartbeat messages
~~~~~~~~~~~~~~~~~~
The :code:`LOVE-Manager` receives heartbeat messages from the different :code:`LOVE-Producer` and :code:`LOVE-Commander` instances.
The heartbeats are stored internally and sent with a certain frequency to the clients subscribed to the :code:`heartbeat-manager-0-stream` group.

The input messages to be received from :code:`LOVE-Producer` and :code:`LOVE-Commander` instances have the following structure:

.. code-block:: json

  {
    "heartbeat": "<component name, e.g. Telemetries>",
    "timestamp": "<timestamp of the last heartbeat>"
  }



The output messages that are sent to clients, have the following structure:

.. code-block:: json

  {
    "category": "heartbeat",
    "data": [
      {
        "csc": "<component name, e.g. Telemetries>",
        "salindex": 0,
        "data": {
          "timestamp": "<timestamp of the last heartbeat>"
        }
      }
    ],
    "subscription": "heartbeat"
  }

Where :code:`data` contains data for each instance of the :code:`LOVE-Producer` and :code:`LOVE-Commander`.

Action messages
~~~~~~~~~~~~~~~
Action messages allow clients to request certain actions from the consumers.
At the moment there is only one action available "get time data", which returns the current server time in various formats.

The expected input message, to be sent by a client, is specified as follows:

.. code-block:: json

  {
    "action": "get_time_data",
    "request_time": "<timestamp with the request time, e.g. 123243423.123>",
  }

And the the expected output, or response, message is specified as follows:

.. code-block:: json

  {
    "time_data": {
      "utc": "<current time in UTC scale as a unix timestamp (seconds)>",
      "tai": "<current time in UTC scale as a unix timestamp (seconds)>",
      "mjd": "<current time as a modified julian date>",
      "sidereal_summit": "<current time as a sidereal_time w/respect to the summit location (hourangles)>",
      "sidereal_summit": "<current time as a sidereal_time w/respect to Greenwich location (hourangles)>",
      "tai_to_utc": "<The number of seconds of difference between TAI and UTC times (seconds)>",
    },
    "request_time": "<timestamp with the request time, e.g. 123243423.123>",
  }

Observing Log messages
~~~~~~~~~~~~~~~~~~~~~~
Observing Log messages are treated by the :code:`LOVE-Manager` like a regular subscription message.
The :code:`LOVE-CSC` subscribes to the group :code:`love_csc-love-0-observingLog`, and clients can send observing logs by sending messages to that group.

The message structure clients must use to send observing logs is the following:

The expected input message, to be sent by a client, is specified as follows:

.. code-block:: json

  {
    "category": "love_csc",
    "data": [
      {
        "csc": "love",
        "salindex": 0,
        "data": {
          "observingLog": {
            "user": "admin",
            "message": "hola"
          }
        }
      }
    ]
  }


Commander and Other actions API
===============================

The :code:`LOVE-Manager` provides HTTP endpoints for requests to the :code:`LOVE-Commander`, as well as other actions.


Command
-------
Requests a command to the :code:`LOVE-Commander`

- Url: :code:`<IP>/manager/api/cmd/`
- HTTP Operation: POST
- Message JSON data:

.. code-block:: json

  {
    "cmd": "<Command name, e.g: cmd_acknowledge>",
    "csc": "<Name of the CSC, e.g: Watcher>",
    "salindex": "<SAL Index in numeric format, e.g. 0>",
    "params": {
      "key1": "value1",
      "key2": "value2",
    },
  }

- Expected Response, if command successful:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "ack": "Done",
    }
  }

- Expected Response, if command timed-out:

.. code-block:: json

  {
    "status": 504,
    "data": {
      "ack": "Command time out",
    }
  }

- Expected Response, command failure:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "ack": "<Text with command result/message>",
    }
  }

Validate Config Schema
----------------------
Validates a given configuration in YAML format with a given schema

- Url: :code:`<IP>/manager/api/validate-config-schema/`
- HTTP Operation: POST
- Message JSON data:

.. code-block:: json

  {
    "config": "<Configuration to validate, in YAML format>",
    "schema": "<Schema to to validate the config against, in YAML format>",
  }

- Expected Response for valid config:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "title": "None",
      "output": "<output message fo the validator>",
    }
  }

- Expected Response for invalid config:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "title": "INVALID CONFIG YAML",
      "error": {
        "message": "<Error message>",
        "path": ["<config_paths>"],
        "schema_path": ["<schema_paths>"],
      },
    }
  }


SAL Info - Metadata
----------------------
Requests SalInfo.metadata from the :code:`LOVE-Commander`.
The response contains the SAL and XML version of the different CSCs.

- Url: :code:`<IP>/manager/api/salinfo/metadata/`
- HTTP Operation: GET

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "<CSC_1>": {
        "sal_version": "<SAL version in format x.x.x>",
        "xml_version": "<XML version in format x.x.x>"
      },
      "<CSC_2>": {
        "sal_version": "<SAL version in format x.x.x>",
        "xml_version": "<XML version in format x.x.x>"
      },
    },
  }

For example:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "Watcher": {
        "sal_version": "4.1.3",
        "xml_version": "1.0.0"
      },
      "MTM1M3": {
        "sal_version": "4.1.3",
        "xml_version": "1.0.0"
      },
      "ATPtg": {
        "sal_version": "4.1.3",
        "xml_version": "1.0.0"
      },
      "ATPneumatics": {
        "sal_version": "4.1.3",
        "xml_version": "1.0.0"
      },
    },
  }


SAL Info - Topic Names
----------------------
Requests SalInfo.topic_names from the :code:`LOVE-Commander`.
The response contains the events, telemetries and command names of each CSC.
The URL accepts :code:`<categories>` as query params, which can be any combination of the following strings separated by "-":
:code:`event`, :code:`telemetry` and :code:`command`. If there is no query param, then all topics are selected.

- Url: :code:`<IP>/manager/api/salinfo/topic-names?categories=<categories>`
- HTTP Operation: GET

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "<CSC_1>": {
        "event_names": ["<event_name_1>", "<event_name_2>"],
        "telemetry_names": ["<telemetry_name_1>", "<telemetry_name_2>"],
        "command_names": ["<command_name_1>", "<command_name_2>"]
      },
      "<CSC_2>": {
        "event_names": ["<event_name_1>", "<event_name_2>"],
        "telemetry_names": ["<telemetry_name_1>", "<telemetry_name_2>"],
        "command_names": ["<command_name_1>", "<command_name_2>"]
      },
    },
  }

For example:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "Watcher": {
        "event_names": [
            "alarm",
            "appliedSettingsMatchStart",
            "authList",
            "errorCode",
            "heartbeat",
            "logLevel",
            "logMessage",
            "settingVersions",
            "settingsApplied",
            "simulationMode",
            "softwareVersions",
            "summaryState"
        ],
        "telemetry_names": [],
        "command_names": [
            "abort",
            "acknowledge",
            "disable",
            "enable",
            "enterControl",
            "exitControl",
            "mute",
            "setAuthList",
            "setLogLevel",
            "setValue",
            "showAlarms",
            "standby",
            "start",
            "unacknowledge",
            "unmute"
        ]
      },
    },
  }

SAL Info - Topic Data
----------------------
Requests SalInfo.topic_data from the :code:`LOVE-Commander`.
The response contains the events, teelemetries and command data of each CSC.
The URL accepts :code:`<categories>` as query params, which can be any combination of the following strings separated by "-":
:code:`event`, :code:`telemetry` and :code:`command`. If there is no query param, then all topics are selected.

- Url: :code:`<IP>/manager/api/salinfo/topic-data?categories=<categories>`
- HTTP Operation: GET

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "<CSC_1>": {
        "event_data": {
          "<parameter_1>": {
            "<field_11>": "<value_11>",
            "<field_12>": "<value_12>",
          },
          "<parameter_2>": {
            "<field_21>": "<value_21>",
            "<field_22>": "<value_22>",
          },
        },
        "telemetry_data": {
          "<parameter_1>": {
            "<field_11>": "<value_11>",
            "<field_12>": "<value_12>",
          },
          "<parameter_2>": {
            "<field_21>": "<value_21>",
            "<field_22>": "<value_22>",
          },
        },
        "command_data": {
          "<parameter_1>": {
            "<field_11>": "<value_11>",
            "<field_12>": "<value_12>",
          },
          "<parameter_2>": {
            "<field_21>": "<value_21>",
            "<field_22>": "<value_22>",
          },
        },
      },
    },
  }


LOVE Config File
----------------------
Requests the LOVE config file.
The response contains the contentes fo the config file (:code:`json` format) as :code:`json`.

- Url: :code:`<IP>/manager/api/config`
- HTTP Operation: GET

- Expected Response:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "alarms": {
        "minSeveritySound": "<'warning', 'serious' or 'critical'>",
        "minSeverityNotification": "<'warning', 'serious' or 'critical'>",
      },
      "camFeeds": {
        "generic": "<URL to the stream for the generic camera, can be a relative URL. E.g: /gencam>",
        "allSky": "<URL to the stream for the all sky camera, can be a relative URL. E.g: /skycam>"
      }
    },
  }


UI Framework
============

The UI Framework backend is composed of 3 models:

  - **Workspace:** represents a workspace, composed by different views
  - **View:** represents a view, all the data of the view is contained in JSON format in the :code:`data` field of the view
  - **WorkspaceView:** relates a Workspace and a View, it is the intermediary table of the many-to-many relationship between Workspace and View.

Currently the API provides a standard REST api to perform CRUD (Create, Retrieve, Update, Delete) operations over these models, plus some other actions.

To try out the API you can either:

  - Use the browsable API available in: :code:`<IP>/manager/ui_framework/`
  - See the apidoc in Swagger format, available in: :code:`<IP>/manager/apidoc/swagger/`
  - See the apidoc in ReDoc format, available in: :code:`<IP>/manager/apidoc/redoc/`


Unauthenticated responses
-------------------------
All requests from unauthenticated users should receive the following response:

.. code-block:: json

  {
    "status": 401
  }


Unauthorized responses
-----------------------
All requests from users who are authenticated but do not have permissions to perform a particular request, should receive the following response:

.. code-block:: json

  {
    "status": 403
  }

Views Requests
--------------
Endpoints to perform CRUD over Views


Create View
~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/views/`
- HTTP Operation: POST
- Request payload: JSON with the fields of the view

.. code-block:: json

  {
    "name": "<View 1 name>",
    "thumbnail": "<location location of the thumbnail, e.g. /media/thumbnails/view_1.png>",
    "data": "<dictionary containing the data of the view>",
  }

- Expected Response: the full content of the view (including its :code:`<id>`)

.. code-block:: json

  {
    "status": 201,
    "data": {
      "id": "<Numeric ID of the view, e.g. 1>",
      "name": "<View 1 name>",
      "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
      "data": "<dictionary containing the data of the view>",
    }
  }


Retrieve Views
~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/views/<id>/`, where the optional parameter :code:`<id>` can be used to retrieve detailed data of a particular view
- HTTP Operation: GET

- Expected Response: if no :code:`<id>` parameter is attached to the URL, then the response is a list of JSONs, 1 for each view. If there is an :code:`<id>` parameter, then response is only the JSON corresponding to that view

.. code-block:: json

  {
    "status": 200,
    "data": [
      {
        "id": "<Numeric ID of the view, e.g. 1>",
        "name": "<View 1 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
        "data": "<dictionary containing the data of the view>",
      },
      {
        "id": "<Numeric ID of the view, e.g. 2>",
        "name": "<View 2 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_2.png>",
        "data": "<dictionary containing the data of the view>",
      },
    ]
  }

Update View
~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/views/<id>/`, where the parameter :code:`<id>` defines the view to edit
- HTTP Operation: PUT
- Request payload: JSON with the fields to change in the view

.. code-block:: json

  {
    "name": "<View 1 name>",
    "thumbnail": "<new location location of the thumbnail>",
    "data": "<dictionary containing the new data of the view>",
  }

- Expected Response: the new content of the view

.. code-block:: json

  {
    "status": 200,
    "data": {
      "id": "<Numeric ID of the view, e.g. 1>",
      "name": "<View 1 name>",
      "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
      "data": "<dictionary containing the data of the view>",
    }
  }

Delete View
~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/views/<id>/`, where the parameter :code:`<id>` defines the view to delete
- HTTP Operation: DELETE

- Expected Response: the new content of the view

.. code-block:: json

  {
    "status": 204
  }

Get Views Summary
~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/views/summary/`
- HTTP Operation: GET

- Expected Response: a list of summarized information of the views, contianing only their :code:`<name>`, :code:`<id>` and :code:`<thumbnail>` 

.. code-block:: json

  {
    "status": 200,
    "data": [
      {
        "id": "<Numeric ID of the view, e.g. 1>",
        "name": "<View 1 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
      },
      {
        "id": "<Numeric ID of the view, e.g. 2>",
        "name": "<View 2 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_2.png>",
      },
      {
        "id": "<Numeric ID of the view, e.g. 3>",
        "name": "<View 3 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_3.png>",
      },
    ]
  }

Search View
~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/views/search/?query=<search_text>`
- HTTP Operation: GET

- Expected Response: a list of views whise names contain the :code:`<search_text>`t passed in the URL.

.. code-block:: json

  {
    "status": 200,
    "data": [
      {
        "id": "<Numeric ID of the view, e.g. 1>",
        "name": "<View 1 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
        "data": "<dictionary containing the data of the view>",
      },
      {
        "id": "<Numeric ID of the view, e.g. 2>",
        "name": "<View 2 name>",
        "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_2.png>",
        "data": "<dictionary containing the data of the view>",
      },
    ]
  }



Workspaces Requests
-------------------
Endpoints to perform CRUD over Workspaces


Create Workspace
~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaces/`
- HTTP Operation: POST
- Request payload: JSON with the fields of the workspace

.. code-block:: json

  {
    "name": "<Workspace 1 name>",
  }

- Expected Response: the full content of the workspace (including its :code:`<id>`)

.. code-block:: json

  {
    "status": 201,
    "data": {
      "id": "<Numeric ID of the workspace, e.g. 1>",
      "name": "<Workspace 1 name>",
      "views": [
        "<view_id1 (this is a list of ids of views)>",
        "<view_id2>",
      ],
      "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
      "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
    }
  }


Retrieve Workspaces
~~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaces/<id>/`, where the optional parameter :code:`<id>` can be used to retrieve detailed data of a particular workspace
- HTTP Operation: GET

- Expected Response: if no :code:`<id>` parameter is attached to the URL, then the response is a list of JSONs, 1 for each workspace. If there is an :code:`<id>` parameter, then response is only the JSON corresponding to that workspace

.. code-block:: json

  {
    "status": 200,
    "data": [
      {
        "id": "<Numeric ID of the workspace, e.g. 1>",
        "name": "<Workspace 1 name>",
        "views": [
          "<view_id1>",
          "<view_id2>",
        ],
        "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
        "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
      },
      {
        "id": "<Numeric ID of the workspace, e.g. 2>",
        "name": "<Workspace 2 name>",
        "views": [
          "<view_id3>",
          "<view_id2>",
        ],
        "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
        "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
      }
    ]
  }

Update Workspace
~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaces/<id>/`, where the parameter :code:`<id>` defines the workspace to edit
- HTTP Operation: PUT
- Request payload: JSON with the fields to change in the workspace

.. code-block:: json

  {
    "name": "<New Workspace 1 name>",
  }

- Expected Response: the new content of the workspace

.. code-block:: json

  {
    "status": 200,
    "data": {
      "id": "<Numeric ID of the workspace, e.g. 1>",
      "name": "<New Workspace 1 name>",
      "views": [
        "<view_id1>",
        "<view_id2>",
      ],
      "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
      "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
    }
  }

Delete Workspace
~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaces/<id>/`, where the parameter :code:`<id>` defines the workspace to delete
- HTTP Operation: DELETE

- Expected Response: the new content of the workspace

.. code-block:: json

  {
    "status": 204
  }


Get Full Workspace
~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaces/<id>/full/`, where the parameter :code:`<id>` defines the workspace to retrieve
- HTTP Operation: GET

- Expected Response: the workspace with its views fully subserialized (list of JSON, instead of list of ids)

.. code-block:: json

  {
    "status": 200,
    "data": {
      "id": "<Numeric ID of the workspace, e.g. 1>",
      "name": "<New Workspace 1 name>",
      "views": [
        {
          "id": "<view_id1>",
          "name": "<View 1 name>",
          "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
          "data": "<dictionary containing the data of the view>",
        },
        {
          "id": "<view_id2>",
          "name": "<View 2 name>",
          "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_2.png>",
          "data": "<dictionary containing the data of the view>",
        },
      ],
      "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
      "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
    }
  }


Get Workspace with Views names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaces/with_view_name/`.
- HTTP Operation: GET

- Expected Response: the workspace with its views subserialized as summary, that is without their :code:`data` fields

.. code-block:: json

  {
    "status": 200,
    "data": [
      {
        "id": "<Numeric ID of the workspace, e.g. 1>",
        "name": "<New Workspace 1 name>",
        "views": [
          {
            "id": "<view_id1>",
            "name": "<View 1 name>",
            "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
          },
          {
            "id": "<view_id2>",
            "name": "<View 2 name>",
            "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_2.png>",
          },
        ],
        "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
        "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
      },
      {
        "id": "<Numeric ID of the workspace, e.g. 2>",
        "name": "<New Workspace 2 name>",
        "views": [
          {
            "id": "<view_id1>",
            "name": "<View 1 name>",
            "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_1.png>",
          },
          {
            "id": "<view_id2>",
            "name": "<View 2 name>",
            "thumbnail": "<location of the view thumbnail, e.g. /media/thumbnails/view_2.png>",
          },
        ],
        "creation_timestamp": "<Timestamp of the creation of the workspace, in ISO format (UTC)>",
        "update_timestamp": "<Timestamp of the last update of the workspace, in ISO format (UTC)>",
      },
    ]
  }


WorkspaceViews Requests
-----------------------
Endpoints to perform CRUD over WorkspaceViews


Create WorkspaceView
~~~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaceviews/`
- HTTP Operation: POST
- Request payload: JSON with the fields of the WorkspaceView

.. code-block:: json

  {
    "view_name": "<Optional name for the view within the conext of the workspace, empty string by default>",
    "sort_value": "<Optional numeric sort vaue to define the order of the views within the workspace, 0 by default>",
    "workspace": "<workspace_id>",
    "view": "<view_id>",
  }

- Expected Response: the full content of the workspace (including its :code:`<id>`)

.. code-block:: json

  {
    "status": 201,
    "data": {
      "id": "<Id of the WorkspaceView>",
      "creation_timestamp": "<Timestamp of the creation of the WorkspaceView, in ISO format (UTC)>",
      "update_timestamp": "<Timestamp of the last update of the WorkspaceView, in ISO format (UTC)>",
      "view_name": "<Optional name for the view within the conext of the workspace, empty string by default>",
      "sort_value": "<Optional numeric sort vaue to define the order of the views within the workspace, 0 by default>",
      "workspace": "<workspace_id>",
      "view": "<view_id>",
    }
  }


Retrieve WorkspaceViews
~~~~~~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaceviews/<id>/`, where the optional parameter :code:`<id>` can be used to retrieve detailed data of a particular WorkspaceView
- HTTP Operation: GET

- Expected Response: if no :code:`<id>` parameter is attached to the URL, then the response is a list of JSONs, 1 for each WorkspaceView. If there is an :code:`<id>` parameter, then response is only the JSON corresponding to that workspace

.. code-block:: json

  {
    "status": 200,
    "data": [
      {
        "id": "<WorkspaceView 1 ID>",
        "creation_timestamp": "<Timestamp of the creation of the WorkspaceView, in ISO format (UTC)>",
        "update_timestamp": "<Timestamp of the last update of the WorkspaceView, in ISO format (UTC)>",
        "view_name": "<View name (optional)>",
        "sort_value": "<Optional sort value>",
        "workspace": "<workspace_id1>",
        "view": "<view_id1>",
      },
      {
        "id": "<WorkspaceView 2 ID>",
        "creation_timestamp": "<Timestamp of the creation of the WorkspaceView, in ISO format (UTC)>",
        "update_timestamp": "<Timestamp of the last update of the WorkspaceView, in ISO format (UTC)>",
        "view_name": "<View name (optional)>",
        "sort_value": "<Optional sort value>",
        "workspace": "<workspace_id1>",
        "view": "<view_id2>",
      },
    ]
  }

Update WorkspaceView
~~~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaceviews/<id>/`, where the parameter :code:`<id>` defines the WorkspaceView to edit
- HTTP Operation: PUT
- Request payload: JSON with the fields to change in the WorkspaceView

.. code-block:: json

  {
    "view_name": "<Optional new name for the view within the conext of the workspace, empty string by default>",
    "sort_value": "<Optional new numeric sort vaue to define the order of the views within the workspace, 0 by default>",
    "workspace": "<workspace_id>",
    "view": "<view_id>",
  }

- Expected Response: the new content of the workspace

.. code-block:: json

  {
    "status": 200,
    "data": {
      "id": "<Id of the WorkspaceView>",
      "creation_timestamp": "<Timestamp of the creation of the WorkspaceView, in ISO format (UTC)>",
      "update_timestamp": "<Timestamp of the last update of the WorkspaceView, in ISO format (UTC)>",
      "view_name": "<Optional name for the view within the conext of the workspace, empty string by default>",
      "sort_value": "<Optional numeric sort vaue to define the order of the views within the workspace, 0 by default>",
      "workspace": "<workspace_id>",
      "view": "<view_id>",
    }
  }

Delete WorkspaceView
~~~~~~~~~~~~~~~~~~~~
- Url: :code:`<IP>/manager/ui_framework/workspaceviews/<id>/`, where the parameter :code:`<id>` defines the WorkspaceView to delete
- HTTP Operation: DELETE

- Expected Response: the new content of the workspace

.. code-block:: json

  {
    "status": 204
  }

LOVE Configuration File
=======================

The config files feature allows loading custom configurations to the LOVE system. These files are uploaded using the LOVE-manager admin platform:

1. Enter http://love-host/manager/admin/. You have to replace **love-host** with the host you are using, e.g. http://love01.cp.lsst.org/manager/admin
2. Login with your admin credentials
3. Then go to http://love-host/manager/admin/api/configfile/ 
4. Select the ADD CONFIG FILE button
5. Enter the required information:
  a. A user must be set
  b. The filename (must include the extension)
  c. The file itself to be loaded
6. Click the SAVE button

The file extension must be json and the format has the form:

.. code-block:: json
  {
    "alarms": {
      "minSeveritySound": "mute",
      "minSeverityNotification": "mute"
    },
    "camFeeds": {
      "startrackera": "/startrackera",
      "startrackerb": "/startrackerb"
    }
  }
This is a normal json file with ``{“key”: “value”}`` items. You can use different variable types such as: strings, numbers, arrays and objects.

Available configurations:

- **alarms**:

  - minSeveritySound: {“mute”, “muted”, “warning”, “serious”, “critical”} : minimum level to reproduce sound alarm notifications. If set to “mute” or “muted” no sound is going to be reproduced.
  - minSeverityNotification: {“mute”, “muted”, “warning”, “serious”, “critical”} : minimum level to report alarm notifications. If set to “mute” or “muted” no alarm will be reported.
- **camFeeds**:

  - startrackera: cam feed used on the GenericCamera component. This feed will be used if the “startrackera” value is set on the FEEDKEY configuration parameter of the GenericCamera or GenericCameraControls components.
  - startrackerb: cam feed used on the GenericCamera component. This feed will be used if the “startrackerb” value is set on the FEEDKEY configuration parameter of the GenericCamera or GenericCameraControls components.
- **efd**:

  - defaultEfdInstance : {“summit_efd”, "ncsa_teststand_efd", “"ldf_stable_efd"”, “ldf_int_efd”, “base_efd”, “tucson_teststand_efd”, “test_efd”} : default efd instance to be queried on the VegaTimeSeriesPlot component.
- **survey**:

  - surveyTime : this is day/time from official start of the surve. Value must be a timestamp in miliseconds (13-digits number) UTC.

EFD
============

Timeseries
~~~~~~~~~~~~~~~~~~~~
Endpoint to request EFD timeseries.

- Url: :code:`<IP>/manager/efd/timeseries`
- HTTP Operation: POST
- Message Payload:

.. code-block:: json

  {
    "start_date": "2020-03-16T12:00:00",
    "time_window": 15,
    "cscs": {
      "ATDome": {
        0: {
          "topic1": ["field1"]
        },
      },
      "ATMCS": {
        1: {
          "topic2": ["field2", "field3"]
        },
      }
    },
    "resample": "1min",
  }
  

- Expected Response, if command successful:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "ATDome-0-topic1": {
        "field1": [
          { ts: "2020-03-06 21:49:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:50:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:51:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:52:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:53:41.471000", value: 0.21 }
        ]
      },
      "ATMCS-1-topic2": {
        "field2": [
          { ts: "2020-03-06 21:49:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:50:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:51:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:52:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:53:41.471000", value: 0.21 }
        ],
        "field3": [
          { ts: "2020-03-06 21:49:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:50:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:51:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:52:41.471000", value: 0.21 },
          { ts: "2020-03-06 21:53:41.471000", value: 0.21 }
        ]
      }
    }
  }



TCS
============

aux
~~~~~~~~~~~~~~~~~~~~
Endpoint to send ATCS commands.

- Url: :code:`<IP>/manager/tcs/aux`
- HTTP Operation: POST
- Message Payload:

.. code-block:: json

  {
    "command_name": "point_azel",
    "params": {
      "az": 30,
      "el": 50
    }
  }
  

- Expected Response, if command successful:

.. code-block:: json

  {
    "status": 200,
    "data": {
      "ack": "Done",
    }
  }

Control Locations
=================

The Control Locations feature allows the user to define a set of locations that can be used to control the telescope. Only one location can be active at a time. The user can define a location by providing a name and a description.

The LOVE system will come with a set of predefined locations that can be used to control the telescope. These locations are:

- **summit**: Cerro Pachon.
- **tucson**: Tucson Control Room.
- **base**: La Serena Control Room.

To set a location of control, the user must activate the specific location through the administration interface (the user can also deactivate the current location of control):

1. Enter http://love-host/manager/admin/. You have to replace **love-host** with the host you are using, e.g. http://love01.cp.lsst.org/manager/admin
2. Login with your admin credentials
3. Go to http://love-host/manager/admin/api/controllocation/ 
4. Select the location you want to activate
5. Mark the "Selected" parameter checkbox
6. Click the SAVE button
