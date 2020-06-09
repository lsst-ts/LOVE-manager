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
        "alarm_sounds": {
          "critical": "<1 or 0>",
          "serious": "<1 or 0>",
          "warning": "<1 or 0>"
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
        "alarm_sounds": {
          "critical": "<1 or 0>",
          "serious": "<1 or 0>",
          "warning": "<1 or 0>"
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
        "alarm_sounds": {
          "critical": "<1 or 0>",
          "serious": "<1 or 0>",
          "warning": "<1 or 0>"
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


Websockets Group Subscriptions
==============================

LOVE-manager Subscriptions scheme
---------------------------------

Group subscriptions are characterized by 4 variables:
* **category:** describe the category or type of stream:
  * ***telemetry:*** streams that transfer data from telemetry systems
  * ***event:*** streams that transfer data from events triggered asynchronously in the system
  * ***cmd:*** streams that transfer acknowledgement messages from sent commands

* **csc:** describes the type of the source CSC, e.g. :code:`ScriptQueue`
* **salindex:** describes the instance number (salindex) of a given the CSC, e.g. :code:`1`
* **stream:** describes the particular stream of the subscription.

The reasoning behind this scheme is that for a given CSC instance e.g. :code:`ScriptQueue 1` (salindex 1), there could be a number of telemetries, events or commands, each identified by a different :code:`stream`.

Accepted messages
-----------------
The consumers accept the following types of messages:

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
Specifying the variables necessary to subscribe a to a group in a JSON message, as follows:

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

Where :code:`{...<data>...}` represents the JSON message that is sent as data.

Command messages
~~~~~~~~~~~~~~~~
Specifying the variables necessary to subscribe a to a group in a JSON message, as follows:

.. code-block:: json

  {
    "category": "cmd",
    "data": [{
      "csc": "ScriptQueue",
      "salindex": 1,
      "data": {
        "cmd": "CommandPath",
        "params": {
          "param1": "value1",
          "param2": "value2",
        },
      }
    }]
  }

Where pairs :code:`param1` and :code:`value1` represent the parameters (name and value) to be passed to the command.


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
