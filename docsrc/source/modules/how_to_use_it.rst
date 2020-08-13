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
- HTTP Operation: post
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
Returns a confirmation of validity, user data, permissions, server_time and (optionally) the LOVE configuraiton file.
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
Returns a confirmation of validity, user data, permissions, server_time and (optionally) the LOVE configuraiton file.
If the :code:`no_config` flag is added to the end of the URL, then the LOVE config files is not read and the corresponding value is returned as :code:`null`

- Url: :code:`<IP>/manager/api/swap-token/` or :code:`<IP>/manager/api/swap-token/no_config/`
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

Logout
------
Requests deletion of a given token, passed through HTTP Headers.
The token is deleted and a confirmation is replied.

- Url: :code:`<IP>/manager/api/logout/`
- HTTP Operation: delete
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
* **category:** describe the category or type of stream:
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
- HTTP Operation: post
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
- HTTP Operation: post
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
- HTTP Operation: get

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
- HTTP Operation: get

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
- HTTP Operation: get

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
- HTTP Operation: get

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

Currently the API provides a standard REST api for these models.
For more info you can either:

  - Use the browsable API available in: :code:`<IP>/manager/ui_framework/`
  - See the apidoc in Swagger format, available in: :code:`<IP>/manager/apidoc/swagger/`
  - See the apidoc in ReDoc format, available in: :code:`<IP>/manager/apidoc/redoc/`
