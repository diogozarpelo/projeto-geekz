from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.orders.models import Order


User = get_user_model()


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.password = "Geekz-Test-Password-2026!"

        self.user = User.objects.create_user(
            email="account-api@example.com",
            password=self.password,
            first_name="Cliente",
            last_name="Geekz",
        )

        self.client = APIClient()

    def register_payload(self, **overrides):
        data = {
            "email": "new-account@example.com",
            "first_name": "Novo",
            "last_name": "Cliente",
            "password": "Geekz-New-Password-2026!",
            "password_confirm": "Geekz-New-Password-2026!",
        }
        data.update(overrides)
        return data

    def authenticate_with_token(self, token):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def test_register_creates_user_and_token(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.register_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)

        user = User.objects.get(
            email="new-account@example.com",
        )

        self.assertEqual(
            response.data["user"]["email"],
            user.email,
        )
        self.assertEqual(
            response.data["user"]["first_name"],
            "Novo",
        )
        self.assertTrue(
            user.check_password(
                "Geekz-New-Password-2026!"
            )
        )
        self.assertNotEqual(
            user.password,
            "Geekz-New-Password-2026!",
        )
        self.assertTrue(
            Token.objects.filter(
                user=user,
                key=response.data["token"],
            ).exists()
        )

    def test_register_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.register_payload(
                email=self.user.email,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.register_payload(
                password_confirm="Different-Password-2026!",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "password_confirm",
            response.data,
        )

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.register_payload(
                password="12345678",
                password_confirm="12345678",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)

    def test_login_returns_token_and_user(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(
            response.data["user"]["email"],
            self.user.email,
        )

        token = Token.objects.get(
            user=self.user,
        )

        self.assertEqual(
            response.data["token"],
            token.key,
        )

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": "Wrong-Password-2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_me_requires_authentication(self):
        response = self.client.get(
            reverse("accounts:me")
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_token_authentication_accesses_me_cart_and_order(self):
        token = Token.objects.create(
            user=self.user,
        )

        order = Order.objects.create(
            user=self.user,
            customer_name="Cliente Geekz",
            customer_email=self.user.email,
            shipping_postal_code="17230-000",
            shipping_street="Rua Teste",
            shipping_number="100",
            shipping_neighborhood="Centro",
            shipping_city="Itapui",
            shipping_state="SP",
            shipping_country="BR",
            subtotal=Decimal("99.90"),
            total_amount=Decimal("99.90"),
        )

        self.authenticate_with_token(token)

        me_response = self.client.get(
            reverse("accounts:me")
        )
        cart_response = self.client.get(
            reverse("cart:active-cart")
        )
        order_response = self.client.get(
            reverse(
                "orders:detail",
                kwargs={
                    "public_id": order.public_id,
                },
            )
        )

        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(order_response.status_code, 200)
        self.assertEqual(
            me_response.data["email"],
            self.user.email,
        )
        self.assertEqual(
            order_response.data["public_id"],
            str(order.public_id),
        )

    def test_logout_revokes_token(self):
        token = Token.objects.create(
            user=self.user,
        )

        self.authenticate_with_token(token)

        logout_response = self.client.post(
            reverse("accounts:logout"),
            {},
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            204,
        )
        self.assertFalse(
            Token.objects.filter(
                user=self.user,
            ).exists()
        )

        me_response = self.client.get(
            reverse("accounts:me")
        )

        self.assertIn(
            me_response.status_code,
            (401, 403),
        )
