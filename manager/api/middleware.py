"""Defines a custom token-based authentication middleware."""


class GetTokenMiddleware(object):
    """The custom token-based authentication middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Remove the HTTP_COOKIE META from requests for tokens.

        Params
        ------
        request: object
            The request object

        Returns
        -------
        Response:
            The corresponding response object
        """
        if request.META['PATH_INFO'] == '/manager/api/get-token/':
            if 'HTTP_COOKIE' in request.META:
                request.META['HTTP_COOKIE'] = ''
        return self.get_response(request)
