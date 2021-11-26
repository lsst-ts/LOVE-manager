from django.test import TestCase, override_settings
from django.urls import reverse
from api.models import Token, CSCAuthorizationRequest
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Permission


@override_settings(DEBUG=True)
class AuthlistTestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        self.client = APIClient()
        user_authlist_obj = {
            "username": "user-authlist",
            "password": "password",
            "email": "test@user.cl",
            "first_name": "user-authlist",
            "last_name": "",
        }
        user_normal_obj = {
            "username": "user-normal",
            "password": "password",
            "email": "test@user.cl",
            "first_name": "user-normal",
            "last_name": "",
        }
        self.user_authlist = User.objects.create_user(
            username=user_authlist_obj["username"],
            password=user_authlist_obj["password"],
            email=user_authlist_obj["email"],
            first_name=user_authlist_obj["first_name"],
            last_name=user_authlist_obj["last_name"],
        )
        self.user_authlist.user_permissions.add(
            Permission.objects.get(name="Access and resolve AuthList requests")
        )
        self.user_normal = User.objects.create_user(
            username=user_normal_obj["username"],
            password=user_normal_obj["password"],
            email=user_normal_obj["email"],
            first_name=user_normal_obj["first_name"],
            last_name=user_normal_obj["last_name"],
        )
        self.token_user_authlist = Token.objects.create(user=self.user_authlist)
        self.token_user_normal = Token.objects.create(user=self.user_normal)

        self.user_authlist_host = f"{self.user_authlist.username}@localhost"
        self.user_normal_host = f"{self.user_normal.username}@localhost"
        self.user_external_host = "user-external@localhost"

        self.req1 = CSCAuthorizationRequest.objects.create(
            user=self.user_normal,
            cscs_to_change="Test:1",
            authorized_users=f"+{self.user_normal_host},-{self.user_external_host}",
            unauthorized_cscs="+ATPtg:0",
            requested_by=self.user_normal_host,
        )

        self.req2 = CSCAuthorizationRequest.objects.create(
            user=self.user_authlist,
            cscs_to_change="Test:1",
            authorized_users=f"-{self.user_normal_host},-{self.user_external_host}",
            unauthorized_cscs="+ATPtg:0",
            requested_by=self.user_normal_host,
        )

        self.req2 = CSCAuthorizationRequest.objects.create(
            user=self.user_authlist,
            cscs_to_change="Test:1",
            authorized_users=f"+{self.user_external_host}",
            unauthorized_cscs="-ATPtg:0",
            requested_by=self.user_normal_host,
        )

    def test_csc_authorization_request_list_authlist_user(self):
        """Test CSCAuthorizationRequest listing for authlist users
        This request should return all available CSCAuthorizationRequest objects
        """
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_authlist.key
        )

        # Act:
        url = reverse("authlistrequest-list")
        response = self.client.get(url, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_csc_authorization_request_list_normal_user(self):
        """Test CSCAuthorizationRequest listing for non authlist users
        This request should return available CSCAuthorizationRequest that were requested by the user
        and also the ones which authorized_users parameter include the user@host
        """
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("authlistrequest-list")
        response = self.client.get(url, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_csc_authorization_create_request_authlist_user(self):
        """Test CSCAuthorizationRequest creation for authlist users
        This request will be created with status = Authorized as the user is in the authlist group
        """
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_authlist.key
        )

        # Act:
        url = reverse("authlistrequest-list")
        payload = {
            "cscs_to_change": "Test:2",
            "authorized_users": f"-{self.user_normal_host},-{self.user_external_host}",
            "unauthorized_cscs": "-MTPtg:0",
            "requested_by": self.user_authlist_host,
            "message": "This will last for 30 minutes.",
            "duration": 30,
        }
        response = self.client.post(url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user_authlist.username)
        self.assertEqual(response.data["cscs_to_change"], payload["cscs_to_change"])
        self.assertEqual(response.data["authorized_users"], payload["authorized_users"])
        self.assertEqual(
            response.data["unauthorized_cscs"], payload["unauthorized_cscs"]
        )
        self.assertEqual(response.data["requested_by"], payload["requested_by"])
        assert response.data["requested_at"] is not None
        self.assertEqual(response.data["message"], payload["message"])
        self.assertEqual(response.data["duration"], payload["duration"])
        self.assertEqual(
            response.data["status"], CSCAuthorizationRequest.RequestStatus.AUTHORIZED
        )
        self.assertEqual(response.data["resolved_by"], self.user_authlist.username)
        assert response.data["resolved_at"] is not None

    def test_csc_authorization_create_request_normal_user(self):
        """Test CSCAuthorizationRequest creation for non authlist users
        This request will be created with status = Pending as the user is not in the authlist group
        """
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("authlistrequest-list")
        payload = {
            "cscs_to_change": "Test:2",
            "authorized_users": f"+{self.user_normal_host},+{self.user_external_host}",
            "unauthorized_cscs": "+MTPtg:0",
            "requested_by": self.user_normal_host,
        }
        response = self.client.post(url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user_normal.username)
        self.assertEqual(response.data["cscs_to_change"], payload["cscs_to_change"])
        self.assertEqual(response.data["authorized_users"], payload["authorized_users"])
        self.assertEqual(
            response.data["unauthorized_cscs"], payload["unauthorized_cscs"]
        )
        self.assertEqual(response.data["requested_by"], payload["requested_by"])
        assert response.data["requested_at"] is not None
        self.assertEqual(
            response.data["status"], CSCAuthorizationRequest.RequestStatus.PENDING
        )
        self.assertEqual(response.data["message"], None)
        self.assertEqual(response.data["duration"], None)
        self.assertEqual(response.data["resolved_by"], None)
        self.assertEqual(response.data["resolved_at"], None)

    def test_csc_authorization_self_remove_normal_user(self):
        """Test CSCAuthorizationRequest with a self removal for non authlist users
        This request will create two instances:
        1. With the information of the request without the self removed user
        2. With just the information of the self removed user. This one will be set with status = Authorized
        """
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_normal.key
        )

        # Act:
        url = reverse("authlistrequest-list")
        payload = {
            "cscs_to_change": "Test:2",
            "authorized_users": f"-{self.user_normal_host},+{self.user_external_host}",
            "unauthorized_cscs": "+MTPtg:0",
            "requested_by": self.user_normal_host,
        }
        removed_payload = {
            "cscs_to_change": "Test:2",
            "authorized_users": f"-{self.user_normal_host}",
            "unauthorized_cscs": "",
            "requested_by": self.user_normal_host,
        }
        new_initial_payload = {
            "cscs_to_change": "Test:2",
            "authorized_users": f"+{self.user_external_host}",
            "unauthorized_cscs": "+MTPtg:0",
            "requested_by": self.user_normal_host,
        }
        response = self.client.post(url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]["user"], self.user_normal.username)
        self.assertEqual(
            response.data[0]["cscs_to_change"], new_initial_payload["cscs_to_change"]
        )
        self.assertEqual(
            response.data[0]["authorized_users"],
            new_initial_payload["authorized_users"],
        )
        self.assertEqual(
            response.data[0]["unauthorized_cscs"],
            new_initial_payload["unauthorized_cscs"],
        )
        self.assertEqual(
            response.data[0]["requested_by"], new_initial_payload["requested_by"]
        )
        assert response.data[0]["requested_at"] is not None
        self.assertEqual(
            response.data[0]["status"], CSCAuthorizationRequest.RequestStatus.PENDING
        )
        self.assertEqual(response.data[0]["duration"], None)
        self.assertEqual(response.data[0]["message"], None)
        self.assertEqual(response.data[0]["resolved_by"], None)
        self.assertEqual(response.data[0]["resolved_at"], None)

        self.assertEqual(response.data[1]["user"], self.user_normal.username)
        self.assertEqual(
            response.data[1]["cscs_to_change"], removed_payload["cscs_to_change"]
        )
        self.assertEqual(
            response.data[1]["authorized_users"], removed_payload["authorized_users"]
        )
        self.assertEqual(
            response.data[1]["unauthorized_cscs"], removed_payload["unauthorized_cscs"]
        )
        self.assertEqual(
            response.data[1]["requested_by"], removed_payload["requested_by"]
        )
        self.assertEqual(
            response.data[1]["status"], CSCAuthorizationRequest.RequestStatus.AUTHORIZED
        )
        self.assertEqual(response.data[1]["resolved_by"], self.user_normal.username)
        self.assertEqual(response.data[1]["duration"], None)
        assert response.data[1]["message"] is not None
        assert response.data[1]["resolved_at"] is not None

    def test_csc_authorization_update_request(self):
        """Test CSCAuthorizationRequest update (approve or deny) for authlist users
        This request will update the specified CSCAuthorizationRequest instance
        """
        # Arrange:
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.token_user_authlist.key
        )

        # Act:
        url = reverse("authlistrequest-detail", args=[self.req1.pk])
        payload = {
            "status": CSCAuthorizationRequest.RequestStatus.AUTHORIZED,
            "message": "This will last for 30 minutes.",
            "duration": 30,
        }
        response = self.client.patch(url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user_normal.username)
        self.assertEqual(response.data["cscs_to_change"], self.req1.cscs_to_change)
        self.assertEqual(response.data["authorized_users"], self.req1.authorized_users)
        self.assertEqual(
            response.data["unauthorized_cscs"], self.req1.unauthorized_cscs
        )
        self.assertEqual(response.data["requested_by"], self.req1.requested_by)
        assert response.data["requested_at"] is not None
        self.assertEqual(
            response.data["status"], CSCAuthorizationRequest.RequestStatus.AUTHORIZED
        )
        self.assertEqual(response.data["message"], "This will last for 30 minutes.")
        self.assertEqual(response.data["duration"], 30)
        self.assertEqual(response.data["resolved_by"], self.user_authlist.username)
        assert response.data["resolved_at"] is not None
