"""Test the UI Framework REST API."""
from django.contrib.auth.models import User, Permission
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

    def test_unauthenticated_list_objects(self):
        """Test that unauthenticated users cannot retrieve the list of objects through the API."""
        for case in self.cases:
            # Act
            url = reverse("{}-list".format(case["key"]))
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Get list of {} did not return status 401".format(case["class"]),
            )

    def test_unauthenticated_create_objects(self):
        """Test that unauthenticated users cannot create objects through the API."""
        for case in self.cases:
            # Act
            url = reverse("{}-list".format(case["key"]))
            response = self.client.post(url, case["new_data"])
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Posting a new {} did not return status 401".format(case["class"]),
            )
            self.assertEqual(
                case["class"].objects.count(),
                case["old_count"],
                "The number of {} should not have changed".format(case["class"]),
            )

    def test_unauthenticated_retrieve_objects(self):
        """Test that unauthenticated users cannot retrieve objects through the API."""
        for case in self.cases:
            # Act
            obj = case["class"].objects.first()
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Getting a {} did not return status 401".format(case["class"]),
            )

    def test_unauthenticated_update_objects(self):
        """Test that unauthenticated users cannot update objects through the API."""
        for case in self.cases:
            # Act
            obj = case["class"].objects.first()
            old_data = get_dict(obj)
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.put(url, case["new_data"])
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Updating a {} did not return status 401".format(case["class"]),
            )
            new_data = get_dict(case["class"].objects.get(pk=obj.pk))
            self.assertEqual(
                new_data,
                old_data,
                "The object {} should not have been updated".format(case["class"]),
            )

    def test_unauthenticated_delete_objects(self):
        """Test that unauthenticated users cannot dalete objects through the API."""
        for case in self.cases:
            # Act
            obj = case["class"].objects.first()
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.delete(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Deleting a {} did not return status 401".format(case["class"]),
            )
            self.assertEqual(
                case["class"].objects.count(),
                case["old_count"],
                "The number of {} should not have changed".format(case["class"]),
            )


class UnauthorizedCrudTestCase(BaseTestCase):
    """Test that unauthorized users cannot use the CRUD API."""

    def setUp(self):
        """Set testcase. Inherits from utils.BaseTestCase."""
        # Arrange
        super().setUp()
        self.login_url = reverse("login")
        self.username = "test"
        self.password = "password"
        self.user = User.objects.create_user(
            username=self.username,
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        self.token = Token.objects.get(user__username=self.username)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_unauthorized_list_objects(self):
        """Test that unauthorized users can still retrieve the list of objects through the API."""
        for case in self.cases:
            # Act
            url = reverse("{}-list".format(case["key"]))
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "Retrieving list of {} did not return status 200".format(case["class"]),
            )
            retrieved_data = [dict(data) for data in response.data]
            self.assertEqual(
                retrieved_data,
                case["current_data"],
                "Retrieved list of {} is not as expected".format(case["class"]),
            )

    def test_unauthorized_create_objects(self):
        """Test that unauthorized users cannot create objects through the API."""
        for case in self.cases:
            # Act
            url = reverse("{}-list".format(case["key"]))
            response = self.client.post(url, case["new_data"])
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                "Posting a new {} did not return status 403".format(case["class"]),
            )
            self.assertEqual(
                case["class"].objects.count(),
                case["old_count"],
                "The number of {} should not have changed".format(case["class"]),
            )

    def test_unauthorized_retrieve_objects(self):
        """Test that unauthorized users can still retrieve objects through the API."""
        for case in self.cases:
            # Act
            obj = case["class"].objects.get(id=case["selected_id"])
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "Getting a {} did not return status 200".format(case["class"]),
            )
            retrieved_data = dict(response.data)
            self.assertEqual(
                retrieved_data,
                case["current_data"][0],
                "Retrieved list of {} is not as expected".format(case["class"]),
            )

    def test_unauthorized_update_objects(self):
        """Test that unauthorized users cannot update objects through the API."""
        for case in self.cases:
            # Act
            obj = case["class"].objects.get(id=case["selected_id"])
            old_data = get_dict(obj)
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.put(url, case["new_data"])
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                "Updating a {} did not return status 403".format(case["class"]),
            )
            new_data = get_dict(case["class"].objects.get(pk=obj.pk))
            self.assertEqual(
                new_data,
                old_data,
                "The object {} should not have been updated".format(case["class"]),
            )

    def test_unauthorized_delete_objects(self):
        """Test that unauthorized users cannot dalete objects through the API."""
        for case in self.cases:
            # Act
            obj = case["class"].objects.first()
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.delete(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                "Deleting a {} did not return status 403".format(case["class"]),
            )
            self.assertEqual(
                case["class"].objects.count(),
                case["old_count"],
                "The number of {} should not have changed".format(case["class"]),
            )


class AuthorizedCrudTestCase(BaseTestCase):
    """Test that authorized users can use the CRUD API."""

    def setUp(self):
        """Set testcase. Inherits from utils.BaseTestCase."""
        # Arrange
        super().setUp()
        self.login_url = reverse("login")
        self.username = "test"
        self.password = "password"
        self.user = User.objects.create_user(
            username=self.username,
            password="password",
            email="test@user.cl",
            first_name="First",
            last_name="Last",
        )
        data = {"username": self.username, "password": self.password}
        self.client.post(self.login_url, data, format="json")
        self.token = Token.objects.get(user__username=self.username)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_authorized_list_objects(self):
        """Test that authorized users can retrieve the list of objects through the API."""
        for case in self.cases:
            # Arrange
            self.user.user_permissions.add(
                Permission.objects.get(codename="view_{}".format(case["key"]))
            )
            # Act
            url = reverse("{}-list".format(case["key"]))
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "Retrieving list of {} did not return status 200".format(case["class"]),
            )
            retrieved_data = [dict(data) for data in response.data]
            expected_data = case["current_data"]
            self.assertEqual(
                retrieved_data,
                expected_data,
                "Retrieved list of {} is not as expected".format(case["class"]),
            )

    def test_authorized_create_objects(self):
        """Test that authorized users can create objects through the API."""
        for case in self.cases:
            # Arrange
            self.user.user_permissions.add(
                Permission.objects.get(codename="add_{}".format(case["key"]))
            )
            # Act
            url = reverse("{}-list".format(case["key"]))
            response = self.client.post(url, case["new_data"])
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Posting a new {} did not return status 201".format(case["class"]),
            )
            self.assertEqual(
                case["class"].objects.count(),
                case["old_count"] + 1,
                "The number of {} should have increased by 1".format(case["class"]),
            )

    def test_authorized_retrieve_objects(self):
        """Test that authorized users can retrieve objects through the API."""
        for case in self.cases:
            # Arrange
            self.user.user_permissions.add(
                Permission.objects.get(codename="view_{}".format(case["key"]))
            )
            # Act
            obj = case["class"].objects.get(id=case["selected_id"])
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.get(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "Getting a {} did not return status 200".format(case["class"]),
            )
            retrieved_data = dict(response.data)
            expected_data = case["current_data"][0]
            self.assertEqual(
                retrieved_data,
                expected_data,
                "Retrieved list of {} is not as expected".format(case["class"]),
            )

    def test_authorized_update_objects(self):
        """Test that authorized users can update objects through the API."""
        for case in self.cases:
            # Arrange
            self.user.user_permissions.add(
                Permission.objects.get(codename="change_{}".format(case["key"]))
            )
            # Act
            obj = case["class"].objects.get(id=case["selected_id"])
            old_data = get_dict(obj)
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.put(url, case["new_data"])
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                "Updating a {} did not return status 200".format(case["class"]),
            )
            new_data = get_dict(case["class"].objects.get(pk=obj.pk))
            self.assertNotEqual(
                new_data,
                old_data,
                "The object {} should have been updated".format(case["class"]),
            )

    def test_authorized_delete_objects(self):
        """Test that authorized users can dalete objects through the API."""
        for case in self.cases:
            # Arrange
            old_count = case["class"].objects.count()
            self.user.user_permissions.add(
                Permission.objects.get(codename="delete_{}".format(case["key"]))
            )
            # Act
            obj = case["class"].objects.first()
            url = reverse("{}-detail".format(case["key"]), kwargs={"pk": obj.pk})
            response = self.client.delete(url)
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_204_NO_CONTENT,
                "Deleting a {} did not return status 204".format(case["class"]),
            )
            self.assertEqual(
                case["class"].objects.count(),
                old_count - 1,
                "The number of {} should have decreased by 1".format(case["class"]),
            )
