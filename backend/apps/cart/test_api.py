from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.catalog.models import Color, Product, ProductVariant, Size

from .models import Cart, CartItem


User = get_user_model()


class CartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="cart-api@example.com",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            email="cart-api-other@example.com",
            password="test-password-123",
        )

        self.color = Color.objects.create(
            name="Preto Cart API",
            slug="preto-cart-api",
            hex_code="#000000",
            is_active=True,
        )

        self.size = Size.objects.create(
            name="M Cart API",
            slug="m-cart-api",
            is_active=True,
        )

        self.product = Product.objects.create(
            name="Camiseta Cart API",
            slug="camiseta-cart-api",
            description="Produto usado nos testes do carrinho.",
            base_price=Decimal("79.90"),
            is_active=True,
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            sku="GEEKZ-CART-API-001",
            price=Decimal("89.90"),
            stock_quantity=5,
            is_active=True,
        )

        self.unavailable_product = Product.objects.create(
            name="Produto Indisponivel Cart API",
            slug="produto-indisponivel-cart-api",
            description="Produto indisponivel.",
            base_price=Decimal("59.90"),
            is_active=False,
        )

        self.unavailable_variant = ProductVariant.objects.create(
            product=self.unavailable_product,
            color=self.color,
            size=self.size,
            sku="GEEKZ-CART-API-INACTIVE",
            stock_quantity=5,
            is_active=True,
        )

        self.client = APIClient()

    def authenticate(self, user=None):
        self.client.force_authenticate(
            user=user or self.user,
        )

    def get_active_cart(self):
        self.authenticate()

        response = self.client.get(
            reverse("cart:active-cart")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        return Cart.objects.get(
            public_id=response.data["public_id"],
        )

    def add_item(self, quantity=1):
        self.authenticate()

        return self.client.post(
            reverse("cart:item-create"),
            {
                "variant_id": self.variant.pk,
                "quantity": quantity,
            },
            format="json",
        )

    def test_active_cart_requires_authentication(self):
        response = self.client.get(
            reverse("cart:active-cart")
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )
        self.assertEqual(
            Cart.objects.count(),
            0,
        )

    def test_active_cart_is_created_for_authenticated_user(self):
        cart = self.get_active_cart()

        self.assertEqual(
            cart.user,
            self.user,
        )
        self.assertEqual(
            cart.status,
            Cart.Status.ACTIVE,
        )
        self.assertEqual(
            Cart.objects.filter(
                user=self.user,
                status=Cart.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_active_cart_is_reused(self):
        self.authenticate()

        first_response = self.client.get(
            reverse("cart:active-cart")
        )
        second_response = self.client.get(
            reverse("cart:active-cart")
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
            first_response.data["public_id"],
            second_response.data["public_id"],
        )
        self.assertEqual(
            Cart.objects.filter(
                user=self.user,
                status=Cart.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_item_can_be_added_to_cart(self):
        response = self.add_item(
            quantity=2,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        item = CartItem.objects.get(
            cart__user=self.user,
            variant=self.variant,
        )

        self.assertEqual(
            item.quantity,
            2,
        )
        self.assertEqual(
            response.data["total_items"],
            2,
        )
        self.assertEqual(
            response.data["subtotal"],
            "179.80",
        )
        self.assertEqual(
            response.data["items"][0]["sku"],
            self.variant.sku,
        )

    def test_adding_same_variant_increments_quantity(self):
        first_response = self.add_item(
            quantity=1,
        )
        second_response = self.add_item(
            quantity=2,
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )
        self.assertEqual(
            second_response.status_code,
            200,
        )

        item = CartItem.objects.get(
            cart__user=self.user,
            variant=self.variant,
        )

        self.assertEqual(
            item.quantity,
            3,
        )
        self.assertEqual(
            CartItem.objects.filter(
                cart__user=self.user,
                variant=self.variant,
            ).count(),
            1,
        )

    def test_adding_quantity_above_stock_is_rejected(self):
        response = self.add_item(
            quantity=6,
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            CartItem.objects.count(),
            0,
        )

    def test_unavailable_variant_cannot_be_added(self):
        self.authenticate()

        response = self.client.post(
            reverse("cart:item-create"),
            {
                "variant_id": self.unavailable_variant.pk,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            CartItem.objects.count(),
            0,
        )

    def test_cart_item_quantity_can_be_updated(self):
        response = self.add_item(
            quantity=1,
        )

        item_id = response.data["items"][0]["id"]

        update_response = self.client.patch(
            reverse(
                "cart:item-detail",
                kwargs={
                    "item_id": item_id,
                },
            ),
            {
                "quantity": 4,
            },
            format="json",
        )

        self.assertEqual(
            update_response.status_code,
            200,
        )

        item = CartItem.objects.get(
            pk=item_id,
        )

        self.assertEqual(
            item.quantity,
            4,
        )
        self.assertEqual(
            update_response.data["subtotal"],
            "359.60",
        )

    def test_invalid_cart_item_quantity_returns_bad_request(self):
        response = self.add_item(
            quantity=1,
        )

        item_id = response.data["items"][0]["id"]

        update_response = self.client.patch(
            reverse(
                "cart:item-detail",
                kwargs={
                    "item_id": item_id,
                },
            ),
            {
                "quantity": 0,
            },
            format="json",
        )

        self.assertEqual(
            update_response.status_code,
            400,
        )

        item = CartItem.objects.get(
            pk=item_id,
        )

        self.assertEqual(
            item.quantity,
            1,
        )

    def test_cart_item_can_be_removed(self):
        response = self.add_item(
            quantity=2,
        )

        item_id = response.data["items"][0]["id"]

        delete_response = self.client.delete(
            reverse(
                "cart:item-detail",
                kwargs={
                    "item_id": item_id,
                },
            )
        )

        self.assertEqual(
            delete_response.status_code,
            200,
        )
        self.assertFalse(
            CartItem.objects.filter(
                pk=item_id,
            ).exists()
        )
        self.assertEqual(
            delete_response.data["total_items"],
            0,
        )
        self.assertEqual(
            delete_response.data["subtotal"],
            "0.00",
        )

    def test_user_cannot_modify_another_users_cart_item(self):
        other_cart = Cart.objects.create(
            user=self.other_user,
        )

        other_item = CartItem.objects.create(
            cart=other_cart,
            variant=self.variant,
            quantity=1,
        )

        self.authenticate()

        response = self.client.patch(
            reverse(
                "cart:item-detail",
                kwargs={
                    "item_id": other_item.pk,
                },
            ),
            {
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        other_item.refresh_from_db()

        self.assertEqual(
            other_item.quantity,
            1,
        )
