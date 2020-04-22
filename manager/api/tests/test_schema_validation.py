from django.test import TestCase, override_settings
from django.urls import reverse
from api.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission
import yaml

@override_settings(DEBUG=True)
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

    def test_syntax_error(self):
        """Test validation output of an unparsable config file"""
        configs = [
            "wait_time: -\na:""",  # ScannerError
            "fail_cleanup: \nw:'",  # ScannerError
            ":"  # ParserError
        ]

        expected_data = [
            {'error': {'context': None,
                       'note': None,
                'problem': 'sequence entries are not allowed here',
                'problem_mark': {'buffer': 'wait_time: -\na:\x00',
                                 'column': 11,
                                 'index': 11,
                                 'line': 0,
                                 'name': '<unicode string>',
                                 'pointer': 11}},
             'title': 'ERROR WHILE PARSING YAML STRING'},
            {'error': {'context': 'while scanning a simple key',
                       'note': None,
                'problem': "could not find expected ':'",
                'problem_mark': {'buffer': "fail_cleanup: \nw:'\x00",
                                 'column': 3,
                                 'index': 18,
                                 'line': 1,
                                 'name': '<unicode string>',
                                 'pointer': 18}},
             'title': 'ERROR WHILE PARSING YAML STRING'},
            {'error': {'context': 'while parsing a block mapping',
                       'note': None,
                'problem': "expected <block end>, but found ':'",
                'problem_mark': {'buffer': ':\x00',
                                 'column': 0,
                                 'index': 0,
                                 'line': 0,
                                 'name': '<unicode string>',
                                 'pointer': 0}},
             'title': 'ERROR WHILE PARSING YAML STRING'}
        ]

        for config, expected_datum in zip(configs, expected_data):
            # Act:
            url = reverse('validate-config-schema')
            request_data = {
                'config': config,
                'schema': self.script_schema
            }
            response = self.client.post(url, request_data, format='json')
            # Assert:
            self.assertEqual(
                response.data,
                expected_datum
            )

    def test_invalid_config(self):
        """Test validation output of an invalid config file"""

        configs = [
            "wait_time: 'asd'",
            "asdfasfd"
        ]

        expected_data = [{
            'error': {
                'message': "'asd' is not of type 'number'",
                'path': ['wait_time'],
                'schema_path': ['properties', 'wait_time', 'type'],
            },
            'title': 'INVALID CONFIG YAML'
        },
            {'error': {'message': 'asdfasfd is not a dict', 'path': [], 'schema_path': []},
             'title': 'INVALID CONFIG YAML'}

        ]

        for config, expected_datum in zip(configs, expected_data):
            # Act:
            url = reverse('validate-config-schema')
            request_data = {
                'config': config,
                'schema': self.script_schema
            }
            response = self.client.post(url, request_data, format='json')

            # Assert:
            self.assertEqual(
                response.data,
                expected_datum
            )
