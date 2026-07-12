from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RouterSanityTests(APITestCase):
    def test_core_services_route(self):
        url = reverse("service-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_projects_check_name_route(self):
        url = reverse("project-check-name")
        response = self.client.get(url)
        # Missing query parameters name/service_type should lead to HTTP 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

