# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed for Inria Chile.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or at your option any later version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


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
        if (
            request.META["PATH_INFO"] == "/manager/api/get-token/"
            and "HTTP_COOKIE" in request.META
        ):
            request.META["HTTP_COOKIE"] = ""
        return self.get_response(request)
