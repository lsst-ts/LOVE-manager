Websockets Connection
=====================

Currently there are 2 ways to establish a websocket connection:

Authenticate with user token
----------------------------
This is the mechanism intended for end users. It requires them to have an authentication token.
In order to stablish the connection they must append the token to the websocket url as follows:

`<IP>/manager/ws/subscription/?token=<my-token>`


Authenticate with password
----------------------------
This is the mechanism intended for other applications. It requires them to have the password token.
In order to stablish the connection they must append the password to the websocket url as follows:

`<IP>/manager/ws/subscription/?password=<my-password>`
