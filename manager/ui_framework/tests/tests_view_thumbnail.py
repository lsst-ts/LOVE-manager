# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Test the UI Framework thumbnail behavior."""

import filecmp
import glob
import os
from unittest import mock

import pytest
import requests
from api.models import Token
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ui_framework.models import View


@override_settings(DEBUG=True)
class ViewThumbnailTestCase(TestCase):
    """Thumbnail files are created and managed properly."""

    def setUp(self):
        """Creates user/client for requests."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_view"),
            Permission.objects.get(codename="add_view"),
            Permission.objects.get(codename="delete_view"),
            Permission.objects.get(codename="change_view"),
        )

        # delete existing test thumbnails
        thumbnail_files_list = glob.glob(settings.MEDIA_ROOT + "/thumbnails/*")
        for file in thumbnail_files_list:
            os.remove(file)

    @override_settings(DEFAULT_FILE_STORAGE="manager.utils.RemoteStorage")
    def test_new_view_from_remote_storage(self):
        """Test thumbnail behavior when adding
        a new view from remote storage."""
        # Arrange
        # read test data (base64 string)
        old_count = View.objects.count()
        mock_location = os.path.join(os.getcwd(), "ui_framework", "tests", "media", "mock", "test")
        with open(mock_location) as f:
            image_data = f.read()

        request_data = {
            "name": "view name",
            "data": {"key1": "value1"},
            "thumbnail": image_data,
        }

        mock_requests_get = mock.patch("requests.get")
        mock_requests_get_client = mock_requests_get.start()
        response_requests_get = requests.Response()
        response_requests_get.status_code = 200
        mock_requests_get_client.return_value = response_requests_get

        mock_requests_post = mock.patch("requests.post")
        mock_requests_post_client = mock_requests_post.start()
        response_requests_post = requests.Response()
        response_requests_post.status_code = 200
        response_requests_post.json = lambda: {
            "ack": "ok",
            "url": "http://foo.bar/file.png",
        }
        mock_requests_post_client.return_value = response_requests_post

        # Act 1
        # send POST request with data
        request_url = reverse("view-list")
        response = self.client.post(request_url, request_data, format="json")

        # Assert
        # - response status code 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # - new object was created
        new_count = View.objects.count()
        self.assertEqual(old_count + 1, new_count)

        # - thumbnail url
        view = View.objects.get(name="view name")
        self.assertEqual(view.thumbnail.url, "http://foo.bar/file.png")

        # - expected response data
        expected_response = {
            "id": view.id,
            "name": "view name",
            "thumbnail": view.thumbnail.url,
            "data": {"key1": "value1"},
            "screen": "desktop",
        }
        self.assertEqual(response.data, expected_response)

        mock_requests_get.stop()
        mock_requests_post.stop()

    def test_new_view(self):
        """Test thumbnail behavior when adding a new view"""
        # Arrange
        # read test data (base64 string)
        old_count = View.objects.count()
        mock_location = os.path.join(os.getcwd(), "ui_framework", "tests", "media", "mock", "test")
        with open(mock_location) as f:
            image_data = f.read()

        request_data = {
            "name": "view name",
            "data": {"key1": "value1"},
            "thumbnail": image_data,
        }
        # Act 1
        # send POST request with data
        request_url = reverse("view-list")
        response = self.client.post(request_url, request_data, format="json")

        # Assert
        # - response status code 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # - new object was created
        new_count = View.objects.count()
        self.assertEqual(old_count + 1, new_count)

        # - thumbnail url
        view = View.objects.get(name="view name")
        self.assertEqual(view.thumbnail.url, f"{settings.MEDIA_URL}thumbnails/view_1.png")

        # - expected response data
        expected_response = {
            "id": view.id,
            "name": "view name",
            "thumbnail": view.thumbnail.url,
            "data": {"key1": "value1"},
            "screen": "desktop",
        }
        self.assertEqual(response.data, expected_response)

        # - stored file content
        thumbnail_url = view.thumbnail.url.replace("/manager/media/", "/")
        file_url = settings.MEDIA_ROOT + thumbnail_url
        expected_url = mock_location + ".png"
        self.assertTrue(
            filecmp.cmp(file_url, expected_url),
            f"\nThe image was not saved as expected\nsaved at {file_url}\nexpected at {expected_url}",
        )

    def test_delete_view(self):
        """Test thumbnail behavior when deleting a view"""
        # Arrange
        # add view with thumbnail
        mock_location = os.path.join(os.getcwd(), "ui_framework", "tests", "media", "mock", "test")
        with open(mock_location) as f:
            image_data = f.read()

        request_data = {
            "name": "view name",
            "data": {"key1": "value1"},
            "thumbnail": image_data,
        }
        request_url = reverse("view-list")
        self.client.post(request_url, request_data, format="json")

        # Act
        # delete the view
        view = View.objects.get(name="view name")
        delete_response = self.client.delete(reverse("view-detail", kwargs={"pk": view.pk}))

        # Assert 2

        # - response status code
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # - file does not exist
        file_url = settings.MEDIA_BASE + view.thumbnail.url
        with pytest.raises(FileNotFoundError):
            f = open(file_url, "r")
            f.close()

        # - getting the file gives 404
        get_deleted_response = self.client.get("/manager" + view.thumbnail.url)
        self.assertEqual(get_deleted_response.status_code, status.HTTP_404_NOT_FOUND)
