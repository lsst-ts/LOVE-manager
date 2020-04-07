from django.test import TestCase, override_settings
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission
import yaml
from unittest.mock import patch, call


@override_settings(DEBUG=True)
class CommanderTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        """Define the test suite setup."""
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

    @patch('urllib.request.urlopen')
    @patch('urllib.request.Request')
    def test_commander_data(self, mock_Request, mock_urlopen):
        """Test commander data can be sent"""
        # Act:
        url = reverse('commander')
        data = {
            'csc': 'Test',
            'salindex': 1,
            'cmd': 'cmd_setScalars',
            'params': {
                'a': 1,
                'b': 2
            }
        }

        with self.assertRaises(AssertionError):
            response = self.client.post(url, data, format='json')
        self.assertEqual(
            mock_Request.call_args,
            call('http://localhost/commander/cmd', method='POST', data=data)
        )
