from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token


class AuthApiTestCase(TestCase):
    """Test suite for users' authentication."""

    def setUp(self):
        """Define the test suite setup"""
        # Arrange:
        self.client = APIClient()
        self.username = 'test'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.username,
            password='password',
            email='test@user.cl',
            first_name='First',
            last_name='Last',
        )
        self.get_token_url = reverse('get-token')
        self.validate_token_url = reverse('validate-token')

    def test_user_get_token(self):
        """ Test that an user can request a token using name and password """
        # Arrange:
        data = {'username': self.username, 'password': self.password}

        # Assert before request:
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')

        # Act:
        response = self.client.post(self.get_token_url, data, format='json')

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 1, 'The user should have a token')

    def test_user_get_token_failed(self):
        """
        Test that an user cannot request a token if the credentials are invalid
        """
        # Arrange:
        data = {'username': self.username, 'password': 'wrong-password'}

        # Assert before request:
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')

        # Act:
        response = self.client.post(self.get_token_url, data, format='json')

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')

    def test_user_validate_token(self):
        """ Test that an user can validate a token """
        # Arrange:
        data = {'username': self.username, 'password': self.password}
        response = self.client.post(self.get_token_url, data, format='json')
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Act:
        response = self.client.get(
            self.validate_token_url, data, format='json'
        )

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {'detail': 'Token is valid'},
            'The response is not as expected'
        )

    def test_user_validate_token_fail(self):
        """ Test that an user fails to validate an invalid token """
        # Arrange:
        data = {'username': self.username, 'password': self.password}
        response = self.client.post(self.get_token_url, data, format='json')
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key+'fake')

        # Act:
        response = self.client.get(
            self.validate_token_url, data, format='json'
        )

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(
            response.data,
            {'detail': 'Token is valid'},
            'The response indicates the validation was correct'
        )

    def test_user_fails_to_validate_expired_token(self):
        """ Test that an user fails to validate an expired token """
        # Arrange:
        data = {'username': self.username, 'password': self.password}
        response = self.client.post(self.get_token_url, data, format='json')
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)
        token.delete()

        # Assert before request:
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')

        # Act:
        response = self.client.get(
            self.validate_token_url, data, format='json'
        )

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(
            response.data,
            {'detail': 'Token is valid'},
            'The response indicates the validation was correct'
        )
