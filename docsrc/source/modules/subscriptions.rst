Websockets Group Subscriptions
==============================

LOVE-manager Subscriptions scheme
---------------------------------

Group subscriptions are characterized by 4 variables:
* **category:** describe the category or type of stream:
  * ***telemetry:*** streams that transfer data from telemetry systems
  * ***event:*** streams that transfer data from events triggered asynchronously in the system
  * ***cmd:*** streams that transfer acknowledgement messages from sent commands

* **csc:** describes the type of the source CSC, e.g. `ScriptQueue`
* **salindex:** describes the instance number (salindex) of a given the CSC, e.g. `1`
* **stream:** describes the particular stream of the subscription.

The reasoning behind this scheme is that for a given CSC instance e.g. `ScriptQueue 1` (salindex 1), there could be a number of telemetries, events or commands, each identified by a different `stream`.

Accepted messages
-----------------
The consumers accept the following types of messages:

Subscription messages
~~~~~~~~~~~~~~~~~~~~~
Specifying the variables necessary to subscribe a to a group in a JSON message, as follows:

.. code-block:: text

  {
    option: 'subscribe'/'unsubscribe',
    category: 'event'/'telemetry'/'cmd',
    csc: 'ScriptQueue',
    salindex: 1,
    stream: 'stream1',
  }

Telemetry or Event messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specifying the variables necessary to subscribe a to a group in a JSON message, as follows:

.. code-block:: text

  {
    category: 'event'/'telemetry',
    data: [{
      csc: 'ScriptQueue',
      salindex: 1,
      data: {
          stream1: {...<data>...},
          stream2: {...<data>...},
      }
    }]
  }

Where `{...<data>...}` represents the JSON message that is sent as data.

Command messages
~~~~~~~~~~~~~~~~
Specifying the variables necessary to subscribe a to a group in a JSON message, as follows:

.. code-block:: text

  {
    category: 'cmd',
    data: [{
      csc: 'ScriptQueue',
      salindex: 1,
      data: {
        cmd: 'CommandPath',
        params: {
          'param1': 'value1',
          'param2': 'value2',
          ...
        },
      }
    }]
  }

Where pairs `param1` and `value1` represent the parameters (name and value) to be passed to the command.
