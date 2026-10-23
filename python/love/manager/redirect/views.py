# This file is part of LOVE-manager.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from urllib.parse import urlencode, urlunparse

from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from redirect.utils import (
    force_actuator_from_id,
    get_chronograf_dashboard_route,
    get_site_url_domain,
)


@api_view(["GET"])
@permission_classes([])
def m1m3_force_actuators_tests_redirect(request, site):
    """Redirect to the m1m3 force actuators tests chronograph dashboard

    Parameters
    ----------
    request : rest_framework.request.Request
        The request object

    site : str
        The site name

    Returns
    -------
    rest_framework.response.Response
        The response object

    Notes
    -----
    If there is an error, the response will be a
    400 error with the error message

    """

    request_params = dict(request.GET.items())
    actuator_id = int(request_params.get("id", 0))

    try:
        start = request_params["lower"]
        end = request_params["upper"]
    except KeyError:
        return Response("Error: lower and upper parameters are required", status=400)

    actuator = force_actuator_from_id(actuator_id)

    def act(index, actuator):
        return 0 if index is None else actuator

    params = {
        "refresh": "Paused",
        "tempVars[x_index]": act(actuator.x_index, actuator.actuator_id),
        "tempVars[y_index]": act(actuator.y_index, actuator.actuator_id),
        "tempVars[z_index]": actuator.actuator_id,
        "tempVars[s_index]": act(actuator.s_index, actuator.actuator_id),
        "lower": start + "Z",
        "upper": end + "Z",
    }

    try:
        url = urlunparse(
            (
                "https",
                get_site_url_domain(site),
                get_chronograf_dashboard_route(site),
                "",
                urlencode(params),
                "",
            )
        )
    except Exception as e:
        return Response("Error: " + str(e), status=400)

    return redirect(url)
