Authentication
==============

LOVE-manager provides a token-based authentication mechanism.
Clients may request a token providing their credentials (username and password).

Token request, validation and logout operations are done via HTTP requests as follows:

Request token
-------------
Requests a new authorization token.
Returns token, user data and permissions

- Url: `<IP>/manager/api/get-token/`
- HTTP Operation: post
- Message JSON data:

.. code-block:: text

  {
    'username': <username>,
    'password': <password>,
  }

- Expected Response:

.. code-block:: text

  {
    status: 200,
    data: {
      token: <token>,
      permissions: {
        execute_commands: <True/False>,
      },
      user_data: {
        username: <username>,
        password: <password>,
      }
    }
  }

Validate token
--------------
Validates a given authorization token, passed through HTTP Headers.
Returns a confirmation of validity, user data and permissions.

- Url: `<IP>/manager/api/validate-token/`
- HTTP Operation: get
- Message HTTP Headers:

.. code-block:: text

  {
    Accept: 'application/json',
    Content-Type: 'application/json',
    Authorization: 'Token <token>'
  }

- Expected Response:

.. code-block:: text

  {
    status: 200,
    data: {
      detail: 'Token is valid',
      permissions: {
        execute_commands: <True/False>,
      },
      user_data: {
        username: <username>,
        password: <password>,
      }
    }
  }

Logout
------
Requests deletion of a given token, passed through HTTP Headers.
The token is deleted and a confirmation is replied.

- Url: `<IP>/manager/api/logout/`
- HTTP Operation: delete
- Message HTTP Headers:

.. code-block:: text

  {
    Accept: 'application/json',
    Content-Type: 'application/json',
    Authorization: 'Token <token>'
  }

- Expected Response:

.. code-block:: text

  {
    status: 204,
    data: {
      detail: 'Logout successful, Token succesfully deleted',
    }
  }
