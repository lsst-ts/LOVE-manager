from django.test import TestCase
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission
import yaml


class SchemaValidationTestCase(TestCase):
    script_schema = """
    $id: https://github.com/lsst-ts/ts_salobj/TestScript.yaml
    $schema: http://json-schema.org/draft-07/schema#
    additionalProperties: false
    description: Configuration for TestScript
    properties:
        fail_cleanup:
            default: false
            description: If true then raise an exception in the "cleanup" method.
            type: boolean
        fail_run:
            default: false
            description: If true then raise an exception in the "run" method afer the "start" checkpoint but before waiting.
            type: boolean
        wait_time:
            default: 0
            description: Time to wait, in seconds
            minimum: 0
            type: number
    required:
    - wait_time
    - fail_run
    - fail_cleanup
    title: TestScript v1
    type: object
    """

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

        data = {'username': self.username, 'password': self.password}
        response = self.client.post(self.login_url, data, format='json')
        token = Token.objects.filter(user__username=self.username).first()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_valid_config(self):
        """Test schema validation works for a valid config yaml string"""
        # Act:
        url = reverse('validate-config-schema')
        data = {
            'config': "wait_time: 3600",
            'schema': self.script_schema
        }
        response = self.client.post(url, data, format='json')

        # Assert:
        expected_data = {
            "title": "None",
            "output": {'wait_time': 3600, 'fail_cleanup': False, 'fail_run': False}
        }

        self.assertEqual(
            response.data,
            expected_data
        )

    def test_unparsable_config(self):
        """Test validation output of an unparsable config file"""

        # Act:
        url = reverse('validate-config-schema')
        config = "wait_time: -\na:"""
        request_data = {
            'config': config,
            'schema': self.script_schema
        }
        response = self.client.post(url, request_data, format='json')

        # Assert:
        expected_data = {
            'error': {
                'context': None,
                'context_mark': None,
                'note': None,
                'problem': 'sequence entries are not allowed here',
                'problem_mark': {
                    'buffer': f"{config}\x00",
                    'column': 11,
                    'index': 11,
                    'line': 0,
                    'name': '<unicode string>',
                    'pointer': 11
                }
            },
            'title': 'ERROR WHILE PARSING YAML STRING'
        }

        self.assertEqual(
            response.data,
            expected_data
        )
