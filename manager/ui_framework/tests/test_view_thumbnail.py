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

    def test_asdf(self):
        self.maxDiff = None
        # data = {'username': self.username, 'password': self.password}
        # response = self.client.post(self.login_url, data, format='json')
        # print('hjola')

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

        # send POST request with data
        request_url = reverse('view-list')
        response = self.client.post(request_url, request_data, format='json')

        # assert response status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert new object was created 
        new_count = View.objects.count()
        self.assertEqual(old_count + 1, new_count)

        # assert expected response
        view = View.objects.get(name="view name")
        expected_response = {
            'id': view.id,
            'name': 'view name',
            'thumbnail': view.thumbnail.url,
            'data': {'key1': 'value1'},
        }
        self.assertEqual(response.data, expected_response)

        # assert file content
        print('\n settings.MEDIA_ROOT', settings.MEDIA_ROOT)
        print('\n settings.TESTING', settings.TESTING)
        
        with open(view.thumbnail.url) as f: 
            print(f)
            raise Exception('ads')
            


    # def test_asdf(self):
    #     # Arrange
    #     expected_data = [
    #         {**w, 'views': [{
    #             'id': v_pk,
    #             'name': v.name,
    #             'thumbnail': settings.MEDIA_URL + v.thumbnail.name,
    #         } for v_pk in w['views'] for v in [View.objects.get(pk=v_pk)]]}
    #         for w in self.workspaces_data
    #     ]
    #     # Act
    #     url = reverse('workspace-with-view-name')
    #     response = self.client.get(url)
    #     # Assert
    #     self.assertEqual(
    #         response.status_code, status.HTTP_200_OK,
    #         'Retrieving list of workspaces did not return status 200'
    #     )
    #     retrieved_data = [dict(data) for data in response.data]
    #     self.assertEqual(
    #         retrieved_data, expected_data,
    #         'Retrieved list of workspaces is not as expected'
    #     )
