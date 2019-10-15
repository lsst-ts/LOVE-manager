"""Test the UI Framework API."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from api.models import Token
from ui_framework.tests.utils import get_dict, BaseTestCase


class UnauthenticatedCrudTestCase(BaseTestCase):
    """Test that unauthenticated users cannot use the CRUD API."""

    def setUp(self):
        """Set testcase. Inherits from utils.BaseTestCase."""
        # Arrange
        super().setUp()

    def test_cannot_list_objects(self):
        """Test that unauthenticated users cannot retrieve the list of objects through the API."""
        for case in self.cases:
            # Act
            url = reverse('{}-list'.format(case['url_key']))
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Get list of {} did not return status 401'.format(case['class'])
            )

    def test_cannot_create_objects(self):
        """Test that unauthenticated users cannot create objects through the API."""
        for case in self.cases:
            # Act
            url = reverse('{}-list'.format(case['url_key']))
            response = self.client.post(url, case['new_data'])
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Posting a new {} did not return status 401'.format(case['class'])
            )
            self.assertEqual(
                case['class'].objects.count(), case['old_count'],
                'The number of {} should not have changed'.format(case['class'])
            )

    def test_cannot_retrieve_objects(self):
        """Test that unauthenticated users cannot retrieve objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Getting a {} did not return status 401'.format(case['class'])
            )

    def test_cannot_update_objects(self):
        """Test that unauthenticated users cannot update objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            old_data = get_dict(obj)
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.put(url, case['new_data'])
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Updating a {} did not return status 401'.format(case['class'])
            )
            new_data = get_dict(case['class'].objects.get(pk=obj.pk))
            self.assertEqual(
                new_data, old_data,
                'The object {} should not have been updated'.format(case['class'])
            )

    def test_cannot_dalete_objects(self):
        """Test that unauthenticated users cannot dalete objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.delete(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                'Deleting a {} did not return status 401'.format(case['class'])
            )
            self.assertEqual(
                case['class'].objects.count(), case['old_count'],
                'The number of {} should not have changed'.format(case['class'])
            )


class UnauthorizedCrudTestCase(BaseTestCase):
    """Test that unauthorized users cannot use the CRUD API."""

    def setUp(self):
        """Set testcase. Inherits from utils.BaseTestCase."""
        # Arrange
        super().setUp()
        self.login_url = reverse('login')
        self.username = 'test'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.username,
            password='password',
            email='test@user.cl',
            first_name='First',
            last_name='Last',
        )
        data = {'username': self.username, 'password': self.password}
        self.client.post(self.login_url, data, format='json')
        self.token = Token.objects.get(user__username=self.username)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_cannot_list_objects(self):
        """Test that unauthenticated users cannot retrieve the list of objects through the API."""
        for case in self.cases:
            # Act
            url = reverse('{}-list'.format(case['url_key']))
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN,
                'Get list of {} did not return status 403'.format(case['class'])
            )

    def test_cannot_create_objects(self):
        """Test that unauthenticated users cannot create objects through the API."""
        for case in self.cases:
            # Act
            url = reverse('{}-list'.format(case['url_key']))
            response = self.client.post(url, case['new_data'])
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN,
                'Posting a new {} did not return status 403'.format(case['class'])
            )
            self.assertEqual(
                case['class'].objects.count(), case['old_count'],
                'The number of {} should not have changed'.format(case['class'])
            )

    def test_cannot_retrieve_objects(self):
        """Test that unauthenticated users cannot retrieve objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN,
                'Getting a {} did not return status 403'.format(case['class'])
            )

    def test_cannot_update_objects(self):
        """Test that unauthenticated users cannot update objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            old_data = get_dict(obj)
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.put(url, case['new_data'])
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN,
                'Updating a {} did not return status 403'.format(case['class'])
            )
            new_data = get_dict(case['class'].objects.get(pk=obj.pk))
            self.assertEqual(
                new_data, old_data,
                'The object {} should not have been updated'.format(case['class'])
            )

    def test_cannot_dalete_objects(self):
        """Test that unauthenticated users cannot dalete objects through the API."""
        for case in self.cases:
            # Act
            obj = case['class'].objects.first()
            url = reverse('{}-detail'.format(case['url_key']), kwargs={'pk': obj.pk})
            response = self.client.delete(url)
            # Assert
            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN,
                'Deleting a {} did not return status 403'.format(case['class'])
            )
            self.assertEqual(
                case['class'].objects.count(), case['old_count'],
                'The number of {} should not have changed'.format(case['class'])
            )
