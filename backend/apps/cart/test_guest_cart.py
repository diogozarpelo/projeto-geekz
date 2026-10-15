from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.catalog.models import (
    Color,
    Product,
    ProductVariant,
    Size,
)

from .models import Cart, CartItem


User = get_user_model()


class GuestCartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="guest-cart@example.com",
            password="test-password-123",
        )

        self.color = Color.objects.create(
            name="Preto Guest Cart",
            slug="preto-guest-cart",
            hex_code="#000000",
            is_active=True,
        )

        self.size = Size.objects.create(
            name="M Guest Cart",
            slug="m-guest-cart",
            is_active=True,
        )

        self.product = Product.objects.create(
            name="Camiseta Guest Cart",
            slug="camiseta-guest-cart",
            description="Produto para carrinho visitante.",
            base_price=Decimal("79.90"),
            is_active=True,
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            sku="GEEKZ-GUEST-CART-001",
            price=Decimal("89.90"),
            stock_quantity=5,
            is_active=True,
        )

        self.client = APIClient()

    def cart_header(self, public_id):
        return {
            "HTTP_X_GEEKZ_CART_ID": str(public_id),
        }

    def test_anonymous_cart_is_reused_by_public_id(self):
        first_response = self.client.get(
            reverse("cart:active-cart")
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        public_id = first_response.data["public_id"]

        second_response = self.client.get(
            reverse("cart:active-cart"),
            **self.cart_header(public_id),
        )

        self.assertEqual(
            second_response.status_code,
            200,
        )
        self.assertEqual(
            second_response.data["public_id"],
            public_id,
        )
        self.assertEqual(
            Cart.objects.filter(
                user__isnull=True,
                status=Cart.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_anonymous_cart_supports_item_lifecycle(self):
        add_response = self.client.post(
            reverse("cart:item-create"),
            {
                "variant_id": self.variant.pk,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(
            add_response.status_code,
            200,
        )

        public_id = add_response.data["public_id"]
        item_id = add_response.data["items"][0]["id"]

        cart = Cart.objects.get(
            public_id=public_id
        )

        self.assertIsNone(
            cart.user
        )

        update_response = self.client.patch(
            reverse(
                "cart:item-detail",
                kwargs={
                    "item_id": item_id,
                },
            ),
            {
                "quantity": 2,
            },
            format="json",
            **self.cart_header(public_id),
        )

        self.assertEqual(
            update_response.status_code,
            200,
        )
        self.assertEqual(
            update_response.data["items"][0]["quantity"],
            2,
        )

        delete_response = self.client.delete(
            reverse(
                "cart:item-detail",
                kwargs={
                    "item_id": item_id,
                },
            ),
            **self.cart_header(public_id),
        )

        self.assertEqual(
            delete_response.status_code,
            200,
        )
        self.assertEqual(
            delete_response.data["total_items"],
            0,
        )

    def test_login_merges_anonymous_cart_into_user_cart(self):
        guest_response = self.client.post(
            reverse("cart:item-create"),
            {
                "variant_id": self.variant.pk,
                "quantity": 2,
            },
            format="json",
        )

        guest_public_id = guest_response.data[
            "public_id"
        ]

        user_cart = Cart.objects.create(
            user=self.user,
            status=Cart.Status.ACTIVE,
        )

        CartItem.objects.create(
            cart=user_cart,
            variant=self.variant,
            quantity=1,
        )

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("cart:active-cart"),
            **self.cart_header(
                guest_public_id
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["public_id"],
            str(user_cart.public_id),
        )
        self.assertEqual(
            response.data["items"][0]["quantity"],
            3,
        )

        guest_cart = Cart.objects.get(
            public_id=guest_public_id
        )

        self.assertEqual(
            guest_cart.status,
            Cart.Status.ABANDONED,
        )

    def test_anonymous_request_cannot_open_user_cart(self):
        user_cart = Cart.objects.create(
            user=self.user,
            status=Cart.Status.ACTIVE,
        )

        CartItem.objects.create(
            cart=user_cart,
            variant=self.variant,
            quantity=2,
        )

        response = self.client.get(
            reverse("cart:active-cart"),
            **self.cart_header(
                user_cart.public_id
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertNotEqual(
            response.data["public_id"],
            str(user_cart.public_id),
        )
        self.assertEqual(
            response.data["total_items"],
            0,
        )
