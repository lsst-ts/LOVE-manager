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
        self.user = User.objects.create_user(
            username=self.username,
            password='password',
            email='test@user.cl',
            first_name='First',
            last_name='Last',
        )
        self.url = reverse('get-token')

    def test_user_login(self):
        """ Test that an user can request a token using name and password """
        # Arrange:
        data = {'username': 'test', 'password': 'password'}

        # Assert before request:
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')

        # Act:
        response = self.client.post(self.url, data, format='json')

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 1, 'The user should have a token')

    def test_user_login_failed(self):
        """
        Test that an user cannot request a token if the credentials are invalid
        """
        # Arrange:
        data = {'username': 'test', 'password': 'wrong-password'}

        # Assert before request:
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')

        # Act:
        response = self.client.post(self.url, data, format='json')

        # Assert after request:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tokens_num = Token.objects.filter(user__username=self.username).count()
        self.assertEqual(tokens_num, 0, 'The user should have no token')
