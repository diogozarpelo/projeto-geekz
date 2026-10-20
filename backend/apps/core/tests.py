from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_returns_ok_when_database_is_available(self):
        response = self.client.get(
            reverse("health-check"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {"status": "ok"},
        )

    @patch(
        "apps.core.views.connection.cursor",
        side_effect=DatabaseError(
            "database credentials must not be exposed"
        ),
    )
    def test_health_check_returns_503_without_exposing_database_error(
        self,
        mocked_cursor,
    ):
        response = self.client.get(
            reverse("health-check"),
        )

        self.assertEqual(
            response.status_code,
            503,
        )
        self.assertEqual(
            response.json(),
            {"status": "unavailable"},
        )
        self.assertNotContains(
            response,
            "database credentials",
            status_code=503,
        )
        mocked_cursor.assert_called_once_with()
