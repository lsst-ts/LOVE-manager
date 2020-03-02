"""Test the UI Framework thumbnail behavior."""
# from django.conf import settings
from manager import settings
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from api.models import Token
from ui_framework.models import View
import os
import glob
import filecmp
from django.test.utils import override_settings


class ViewThumbnailTestCase(TestCase):
    """Thumbnail files are created and managed properly."""

    def setUp(self):
        """Creates user/client for requests."""
        # Arrange
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='an user',
            password='password',
            email='test@user.cl',
            first_name='First',
            last_name='Last',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.user.user_permissions.add(Permission.objects.get(codename='view_view'),
                                       Permission.objects.get(codename='add_view'),
                                       Permission.objects.get(codename='delete_view'),
                                       Permission.objects.get(codename='change_view'))

        # delete existing test thumbnails
        thumbnail_files_list = glob.glob(settings.MEDIA_ROOT + '/thumbnails/*')
        for file in thumbnail_files_list:
            os.remove(file)

    @override_settings(DEBUG=True)
    def test_new_view(self):
        """ Test thumbnail behavior when adding a new view """
        # Arrange
        # read test data (base64 string)
        old_count = View.objects.count()
        mock_location = os.path.join(os.getcwd(), 'ui_framework', 'tests', 'media', 'mock', 'test')
        with open(mock_location) as f:
            image_data = f.read()

        request_data = {
            "name": "view name",
            "data": {"key1": "value1"},
            "thumbnail": image_data
        }

        # Act
        # send POST request with data
        request_url = reverse('view-list')
        response = self.client.post(request_url, request_data, format='json')

        # Assert
        # - response status code 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # - new object was created
        new_count = View.objects.count()
        self.assertEqual(old_count + 1, new_count)

        # - thumbnail url
        view = View.objects.get(name="view name")
        self.assertEqual(view.thumbnail.url, '/media/thumbnails/view_1.png')

        # - expected response data
        expected_response = {
            'id': view.id,
            'name': 'view name',
            'thumbnail': view.thumbnail.url,
            'data': {'key1': 'value1'},
        }
        self.assertEqual(response.data, expected_response)

        # - stored file content
        file_url = settings.MEDIA_BASE + view.thumbnail.url
        expected_url = mock_location + '.png'
        self.assertTrue(filecmp.cmp(file_url, expected_url),
         f'\nThe image was not saved as expected\nsaved at {file_url}\nexpected at {expected_url}')

        # - retrieved file content from get/ endpoint
        with open(file_url, 'rb') as f:
            file_content = f.read()
            png_response = self.client.get('/manager' + view.thumbnail.url)
            stream = b''.join(png_response.streaming_content)
            self.assertEqual(stream, file_content)
