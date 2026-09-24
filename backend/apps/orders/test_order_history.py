from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Order


User = get_user_model()


class OrderHistoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="history@example.com",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            email="other-history@example.com",
            password="test-password-123",
        )

        self.client = APIClient()
        self.url = reverse("orders:list")

    def create_order(
        self,
        *,
        user=None,
        customer_name="Cliente Historico",
        total_amount=Decimal("100.00"),
    ):
        return Order.objects.create(
            user=user or self.user,
            customer_name=customer_name,
            customer_email=(
                user.email
                if user is not None
                else self.user.email
            ),
            shipping_postal_code="17230-000",
            shipping_street="Rua Teste",
            shipping_number="123",
            shipping_neighborhood="Centro",
            shipping_city="Itapui",
            shipping_state="SP",
            shipping_country="BR",
            subtotal=total_amount,
            total_amount=total_amount,
        )

    def test_order_history_requires_authentication(self):
        response = self.client.get(
            self.url,
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_order_history_returns_only_current_users_orders(self):
        own_order = self.create_order(
            customer_name="Pedido do Usuario",
        )

        self.create_order(
            user=self.other_user,
            customer_name="Pedido de Outro Usuario",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            len(response.data["results"]),
            1,
        )
        self.assertEqual(
            response.data["results"][0]["public_id"],
            str(own_order.public_id),
        )
        self.assertEqual(
            response.data["results"][0]["customer_name"],
            "Pedido do Usuario",
        )

    def test_order_history_returns_multiple_orders(self):
        first_order = self.create_order(
            customer_name="Primeiro Pedido",
            total_amount=Decimal("80.00"),
        )
        second_order = self.create_order(
            customer_name="Segundo Pedido",
            total_amount=Decimal("120.00"),
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            len(response.data["results"]),
            2,
        )

        returned_ids = {
            item["public_id"]
            for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(first_order.public_id),
                str(second_order.public_id),
            },
        )

    def test_order_history_is_ordered_by_newest_first(self):
        first_order = self.create_order(
            customer_name="Pedido Antigo",
        )
        second_order = self.create_order(
            customer_name="Pedido Novo",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["results"][0]["public_id"],
            str(second_order.public_id),
        )
        self.assertEqual(
            response.data["results"][1]["public_id"],
            str(first_order.public_id),
        )

    def test_order_history_is_paginated(self):
        self.create_order(
            customer_name="Pedido Um",
        )
        self.create_order(
            customer_name="Pedido Dois",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.url,
            {
                "page_size": 1,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["count"],
            2,
        )
        self.assertEqual(
            len(response.data["results"]),
            1,
        )
        self.assertIsNotNone(
            response.data["next"],
        )
