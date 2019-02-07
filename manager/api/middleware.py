class GetTokenMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META['PATH_INFO'] == '/api/get-token/':
            if 'HTTP_COOKIE' in request.META:
                request.META['HTTP_COOKIE'] = ''
        return self.get_response(request)
