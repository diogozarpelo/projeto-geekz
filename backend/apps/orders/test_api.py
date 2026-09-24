from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Color, Product, ProductVariant, Size

from .models import Order, Payment
from .providers.mercado_pago import MercadoPagoError


User = get_user_model()


class OrderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="api-customer@example.com",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            email="other-api-customer@example.com",
            password="test-password-123",
        )

        self.color = Color.objects.create(
            name="Preto API",
            slug="preto-api",
            hex_code="#000000",
        )
        self.size = Size.objects.create(
            name="M API",
            slug="m-api",
        )
        self.product = Product.objects.create(
            name="Camiseta API",
            slug="camiseta-api",
            description="Produto usado nos testes HTTP da API.",
            base_price=Decimal("79.90"),
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            sku="GEEKZ-API-001",
            price=Decimal("89.90"),
            stock_quantity=10,
            is_active=True,
        )

        self.cart = Cart.objects.create(
            user=self.user,
        )
        CartItem.objects.create(
            cart=self.cart,
            variant=self.variant,
            quantity=2,
        )

        self.client = APIClient()

    def authenticate(self, user=None):
        self.client.force_authenticate(
            user=user or self.user,
        )

    def checkout_payload(self, **overrides):
        data = {
            "cart_public_id": str(self.cart.public_id),
            "customer_name": "Cliente API",
            "customer_email": "api-customer@example.com",
            "shipping_postal_code": "17230-000",
            "shipping_street": "Rua API",
            "shipping_number": "123",
            "shipping_complement": "Casa",
            "shipping_neighborhood": "Centro",
            "shipping_city": "Itapui",
            "shipping_state": "SP",
            "shipping_country": "BR",
            "notes": "Pedido criado pela API.",
        }
        data.update(overrides)
        return data

    def create_order(self):
        self.authenticate()

        response = self.client.post(
            reverse("orders:checkout"),
            self.checkout_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        return Order.objects.get(
            public_id=response.data["public_id"],
        )

    def test_checkout_requires_authentication(self):
        response = self.client.post(
            reverse("orders:checkout"),
            self.checkout_payload(),
            format="json",
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )
        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_checkout_creates_order_and_converts_cart(self):
        self.authenticate()

        response = self.client.post(
            reverse("orders:checkout"),
            self.checkout_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(
            public_id=response.data["public_id"],
        )

        self.cart.refresh_from_db()
        self.variant.refresh_from_db()

        self.assertEqual(
            order.user,
            self.user,
        )
        self.assertEqual(
            order.customer_name,
            "Cliente API",
        )
        self.assertEqual(
            order.subtotal,
            Decimal("179.80"),
        )
        self.assertEqual(
            order.shipping_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.discount_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.total_amount,
            Decimal("179.80"),
        )
        self.assertEqual(
            order.items.count(),
            1,
        )
        self.assertEqual(
            self.cart.status,
            Cart.Status.CONVERTED,
        )
        self.assertEqual(
            self.variant.stock_quantity,
            8,
        )
        self.assertEqual(
            response.data["total_amount"],
            "179.80",
        )

    def test_checkout_ignores_client_financial_amounts(self):
        self.authenticate()

        payload = self.checkout_payload(
            shipping_amount="999.00",
            discount_amount="999.00",
        )

        response = self.client.post(
            reverse("orders:checkout"),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            public_id=response.data["public_id"],
        )

        self.assertEqual(
            order.shipping_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.discount_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.total_amount,
            Decimal("179.80"),
        )

    def test_checkout_cannot_use_another_users_cart(self):
        self.authenticate(
            self.other_user,
        )

        response = self.client.post(
            reverse("orders:checkout"),
            self.checkout_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )
        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_user_can_retrieve_own_order(self):
        order = self.create_order()

        response = self.client.get(
            reverse(
                "orders:detail",
                kwargs={
                    "public_id": order.public_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["public_id"],
            str(order.public_id),
        )
        self.assertEqual(
            len(response.data["items"]),
            1,
        )

    def test_user_cannot_retrieve_another_users_order(self):
        order = self.create_order()

        self.authenticate(
            self.other_user,
        )

        response = self.client.get(
            reverse(
                "orders:detail",
                kwargs={
                    "public_id": order.public_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    @patch("apps.orders.views.MercadoPagoProvider")
    def test_payment_attempt_is_created_for_order(
        self,
        provider_class,
    ):
        provider_class.return_value.create_pix_order.side_effect = (
            lambda *, payment: payment
        )

        order = self.create_order()

        response = self.client.post(
            reverse(
                "orders:payment-attempt",
                kwargs={
                    "public_id": order.public_id,
                },
            ),
            {
                "method": Payment.Method.PIX,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["method"],
            Payment.Method.PIX,
        )
        self.assertEqual(
            response.data["status"],
            Payment.Status.PENDING,
        )
        self.assertEqual(
            response.data["amount"],
            "179.80",
        )
        self.assertEqual(
            Payment.objects.filter(
                order=order,
            ).count(),
            1,
        )

        provider_class.return_value.create_pix_order.assert_called_once()

    @patch("apps.orders.views.MercadoPagoProvider")
    def test_pending_payment_attempt_is_reused_by_api(
        self,
        provider_class,
    ):
        provider_class.return_value.create_pix_order.side_effect = (
            lambda *, payment: payment
        )

        order = self.create_order()

        url = reverse(
            "orders:payment-attempt",
            kwargs={
                "public_id": order.public_id,
            },
        )

        first_response = self.client.post(
            url,
            {
                "method": Payment.Method.PIX,
            },
            format="json",
        )
        second_response = self.client.post(
            url,
            {
                "method": Payment.Method.PIX,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )
        self.assertEqual(
            second_response.status_code,
            200,
        )
        self.assertEqual(
            first_response.data["id"],
            second_response.data["id"],
        )
        self.assertEqual(
            Payment.objects.filter(
                order=order,
            ).count(),
            1,
        )

    @patch("apps.orders.views.MercadoPagoProvider")
    def test_pix_payment_returns_provider_data(
        self,
        provider_class,
    ):
        def create_pix_order(*, payment):
            payment.provider_order_id = "ORD-API-001"
            payment.external_id = "PAY-API-001"
            payment.provider_data = {
                "order_status": "action_required",
                "order_status_detail": "waiting_transfer",
                "payment_status": "action_required",
                "payment_status_detail": "waiting_transfer",
                "ticket_url": "https://mercadopago.example/pix",
                "qr_code": "000201010212PIXAPI",
                "qr_code_base64": "BASE64-PIX-API",
            }
            payment.idempotency_key = "internal-test-key"
            payment.save(
                update_fields=(
                    "provider_order_id",
                    "external_id",
                    "provider_data",
                    "idempotency_key",
                    "updated_at",
                )
            )
            return payment

        provider_class.return_value.create_pix_order.side_effect = (
            create_pix_order
        )

        order = self.create_order()

        response = self.client.post(
            reverse(
                "orders:payment-attempt",
                kwargs={
                    "public_id": order.public_id,
                },
            ),
            {
                "method": Payment.Method.PIX,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["provider_order_id"],
            "ORD-API-001",
        )
        self.assertEqual(
            response.data["external_id"],
            "PAY-API-001",
        )
        self.assertEqual(
            response.data["provider_data"]["qr_code"],
            "000201010212PIXAPI",
        )
        self.assertEqual(
            response.data["provider_data"]["ticket_url"],
            "https://mercadopago.example/pix",
        )
        self.assertNotIn(
            "idempotency_key",
            response.data,
        )

    @patch("apps.orders.views.MercadoPagoProvider")
    def test_pix_provider_failure_returns_bad_gateway(
        self,
        provider_class,
    ):
        provider_class.return_value.create_pix_order.side_effect = (
            MercadoPagoError(
                "Temporary Mercado Pago failure."
            )
        )

        order = self.create_order()

        response = self.client.post(
            reverse(
                "orders:payment-attempt",
                kwargs={
                    "public_id": order.public_id,
                },
            ),
            {
                "method": Payment.Method.PIX,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            502,
        )
        self.assertIn(
            "detail",
            response.data,
        )

        payment = Payment.objects.get(
            order=order,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_credit_card_payment_method_is_not_available(self):
        order = self.create_order()

        response = self.client.post(
            reverse(
                "orders:payment-attempt",
                kwargs={
                    "public_id": order.public_id,
                },
            ),
            {
                "method": Payment.Method.CREDIT_CARD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertIn(
            "method",
            response.data,
        )
        self.assertEqual(
            Payment.objects.filter(
                order=order,
            ).count(),
            0,
        )

    def test_invalid_payment_method_returns_bad_request(self):
        order = self.create_order()

        response = self.client.post(
            reverse(
                "orders:payment-attempt",
                kwargs={
                    "public_id": order.public_id,
                },
            ),
            {
                "method": "boleto-invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            Payment.objects.filter(
                order=order,
            ).count(),
            0,
        )
