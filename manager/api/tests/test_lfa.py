from unittest.mock import patch, Mock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.utils.datastructures import MultiValueDict
from api.views import lfa


@override_settings(DEBUG=True)
class LFATestCase(TestCase):
    def setUp(self):
        """Define the test suite setup."""
        # Arrange
        pass

    @patch("requests.post")
    def test_no_files_uploaded(self, mock_post):
        request = HttpRequest()
        request.FILES = MultiValueDict()
        response = lfa(request, option="upload-file")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"ack": "No files to upload"})

    @patch("requests.post")
    def test_successful_file_upload(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "http://example.com/uploaded-file"}
        mock_post.return_value = mock_response

        request = HttpRequest()
        request.FILES["file[]"] = [SimpleUploadedFile("test.txt", b"file_content")]
        response = lfa(request, option="upload-file")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "ack": "All files uploaded correctly",
                "urls": ["http://example.com/uploaded-file"],
            },
        )

    @patch("requests.post")
    def test_successful_multiple_file_upload(self, mock_post):
        # Create mock responses for the API
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"url": "http://example.com/uploaded-file1"}

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"url": "http://example.com/uploaded-file2"}

        mock_post.side_effect = [
            mock_response1,
            mock_response2,
        ]  # Mock responses for multiple file uploads

        request = HttpRequest()
        uploaded_file1 = SimpleUploadedFile("test1.txt", b"file_content_1")
        uploaded_file2 = SimpleUploadedFile("test2.txt", b"file_content_2")
        request.FILES = MultiValueDict({"file[]": [uploaded_file1, uploaded_file2]})

        response = lfa(request, option="upload-file")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "ack": "All files uploaded correctly",
                "urls": [
                    "http://example.com/uploaded-file1",
                    "http://example.com/uploaded-file2",
                ],
            },
        )

    @patch("requests.post")
    def test_failed_file_upload(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        request = HttpRequest()
        request.FILES["file[]"] = [SimpleUploadedFile("test.txt", b"file_content")]
        response = lfa(request, option="upload-file")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"ack": "Error when uploading files"})

    def test_invalid_option(self):
        request = HttpRequest()
        request.FILES["file[]"] = [SimpleUploadedFile("test.txt", b"file_content")]
        response = lfa(request, option="invalid-option")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"ack": "Option not found"})
