from django.test import TestCase
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission

class SchemaValidationTestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
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
        self.user.user_permissions.add(Permission.objects.get(name='Execute Commands'))
        self.login_url = reverse('login')
        self.validate_token_url = reverse('validate-token')
        self.logout_url = reverse('logout')
        self.expected_permissions = {
            'execute_commands': True,
        }


    def test_validation(self):
        """Test schema validation can be performed"""
        # Arrange:
        data = {'username': self.username, 'password': self.password}
        response = self.client.post(self.login_url, data, format='json')
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Act:
        url = reverse('validate-config-schema')
        data = {'data': 'adsfasdf'}
        response = self.client.post(url, data, format='json')
        print('response', response)
        print('response.data', response, flush=True)