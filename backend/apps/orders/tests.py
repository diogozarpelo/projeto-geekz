from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Color, Product, ProductVariant, Size

from .models import Order, OrderItem, Payment
from .payment_services import PaymentError, create_payment_attempt
from .services import OrderConversionError, convert_cart_to_order


User = get_user_model()


class ConvertCartToOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="customer@example.com",
            password="test-password-123",
        )

        self.color = Color.objects.create(
            name="Preto Teste",
            slug="preto-test",
            hex_code="#000000",
        )

        self.size = Size.objects.create(
            name="M Test",
            slug="m-test",
        )

        self.product = Product.objects.create(
            name="Camiseta Teste",
            slug="camiseta-teste",
            description="Produto usado nos testes de pedidos.",
            base_price=Decimal("79.90"),
            is_active=True,
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            sku="GEEKZ-TEST-001",
            price=Decimal("89.90"),
            stock_quantity=10,
            is_active=True,
        )

        self.cart = Cart.objects.create(
            user=self.user,
        )

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            variant=self.variant,
            quantity=2,
        )

    def convert_cart(self, **overrides):
        data = {
            "cart": self.cart,
            "customer_name": "Cliente Teste",
            "customer_email": "customer@example.com",
            "shipping_postal_code": "17230-000",
            "shipping_street": "Rua Teste",
            "shipping_number": "123",
            "shipping_complement": "Apto 4",
            "shipping_neighborhood": "Centro",
            "shipping_city": "Itapui",
            "shipping_state": "SP",
            "shipping_country": "BR",
            "shipping_amount": Decimal("15.00"),
            "discount_amount": Decimal("10.00"),
            "notes": "Pedido de teste",
        }
        data.update(overrides)

        return convert_cart_to_order(**data)

    def test_convert_cart_creates_order_and_updates_stock_and_cart(self):
        order = self.convert_cart()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.customer_name, "Cliente Teste")
        self.assertEqual(order.customer_email, "customer@example.com")

        self.assertEqual(order.shipping_postal_code, "17230-000")
        self.assertEqual(order.shipping_street, "Rua Teste")
        self.assertEqual(order.shipping_number, "123")
        self.assertEqual(order.shipping_complement, "Apto 4")
        self.assertEqual(order.shipping_neighborhood, "Centro")
        self.assertEqual(order.shipping_city, "Itapui")
        self.assertEqual(order.shipping_state, "SP")
        self.assertEqual(order.shipping_country, "BR")

        self.assertEqual(order.subtotal, Decimal("179.80"))
        self.assertEqual(order.shipping_amount, Decimal("15.00"))
        self.assertEqual(order.discount_amount, Decimal("10.00"))
        self.assertEqual(order.total_amount, Decimal("184.80"))

        order_item = order.items.get()

        self.assertEqual(order_item.variant, self.variant)
        self.assertEqual(order_item.product_name, "Camiseta Teste")
        self.assertEqual(order_item.sku, "GEEKZ-TEST-001")
        self.assertEqual(order_item.color_name, "Preto Teste")
        self.assertEqual(order_item.size_name, "M Test")
        self.assertEqual(order_item.unit_price, Decimal("89.90"))
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.total_price, Decimal("179.80"))

        self.variant.refresh_from_db()
        self.cart.refresh_from_db()

        self.assertEqual(self.variant.stock_quantity, 8)
        self.assertEqual(self.cart.status, Cart.Status.CONVERTED)

    def test_order_item_snapshot_does_not_change_with_catalog(self):
        order = self.convert_cart()
        order_item = order.items.get()

        self.product.name = "Nome Alterado"
        self.product.base_price = Decimal("999.00")
        self.product.save()

        self.variant.sku = "SKU-ALTERADO"
        self.variant.price = Decimal("500.00")
        self.variant.save()

        self.color.name = "Cor Alterada"
        self.color.save()

        self.size.name = "Tamanho Alterado"
        self.size.save()

        order_item.refresh_from_db()

        self.assertEqual(order_item.product_name, "Camiseta Teste")
        self.assertEqual(order_item.sku, "GEEKZ-TEST-001")
        self.assertEqual(order_item.color_name, "Preto Teste")
        self.assertEqual(order_item.size_name, "M Test")
        self.assertEqual(order_item.unit_price, Decimal("89.90"))

    def test_empty_cart_cannot_be_converted(self):
        empty_cart = Cart.objects.create()

        with self.assertRaisesMessage(
            OrderConversionError,
            "An empty cart cannot be converted into an order.",
        ):
            convert_cart_to_order(
                cart=empty_cart,
                customer_name="Cliente Teste",
                customer_email="customer@example.com",
                shipping_postal_code="17230-000",
                shipping_street="Rua Teste",
                shipping_number="123",
                shipping_neighborhood="Centro",
                shipping_city="Itapui",
                shipping_state="SP",
            )

        self.assertEqual(Order.objects.count(), 0)

        empty_cart.refresh_from_db()
        self.assertEqual(empty_cart.status, Cart.Status.ACTIVE)

    def test_required_shipping_address_blocks_conversion(self):
        with self.assertRaisesMessage(
            OrderConversionError,
            "Shipping city is required.",
        ):
            self.convert_cart(shipping_city="")

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

        self.variant.refresh_from_db()
        self.cart.refresh_from_db()

        self.assertEqual(self.variant.stock_quantity, 10)
        self.assertEqual(self.cart.status, Cart.Status.ACTIVE)

    def test_insufficient_stock_rolls_back_conversion(self):
        self.variant.stock_quantity = 1
        self.variant.save(update_fields=("stock_quantity",))

        with self.assertRaisesMessage(
            OrderConversionError,
            'Insufficient stock for variant "GEEKZ-TEST-001".',
        ):
            self.convert_cart()

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

        self.variant.refresh_from_db()
        self.cart.refresh_from_db()

        self.assertEqual(self.variant.stock_quantity, 1)
        self.assertEqual(self.cart.status, Cart.Status.ACTIVE)

    def test_same_cart_cannot_be_converted_twice(self):
        first_order = self.convert_cart()

        with self.assertRaisesMessage(
            OrderConversionError,
            "Only active carts can be converted into orders.",
        ):
            self.convert_cart()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        self.variant.refresh_from_db()
        self.cart.refresh_from_db()

        self.assertEqual(first_order.pk, Order.objects.get().pk)
        self.assertEqual(self.variant.stock_quantity, 8)
        self.assertEqual(self.cart.status, Cart.Status.CONVERTED)

class PaymentAttemptTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            customer_name="Cliente Pagamento",
            customer_email="payment@example.com",
            total_amount=Decimal("184.80"),
        )

    def test_create_payment_attempt_creates_pending_pix_payment(self):
        payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.method, Payment.Method.PIX)
        self.assertEqual(
            payment.provider,
            Payment.Provider.MERCADO_PAGO,
        )
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, Decimal("184.80"))
        self.assertEqual(payment.external_id, "")

    def test_pending_payment_attempt_is_reused(self):
        first_payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

        second_payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(first_payment.pk, second_payment.pk)

    def test_paid_order_cannot_receive_new_payment(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=("payment_status",))

        with self.assertRaisesMessage(
            PaymentError,
            "This order is already paid.",
        ):
            create_payment_attempt(
                order=self.order,
                method=Payment.Method.PIX,
            )

        self.assertEqual(Payment.objects.count(), 0)

    def test_cancelled_order_cannot_receive_payment(self):
        self.order.status = Order.Status.CANCELLED
        self.order.save(update_fields=("status",))

        with self.assertRaisesMessage(
            PaymentError,
            "Cancelled orders cannot receive payments.",
        ):
            create_payment_attempt(
                order=self.order,
                method=Payment.Method.PIX,
            )

        self.assertEqual(Payment.objects.count(), 0)

    def test_zero_total_order_does_not_require_payment(self):
        self.order.total_amount = Decimal("0.00")
        self.order.save(update_fields=("total_amount",))

        with self.assertRaisesMessage(
            PaymentError,
            "Orders with zero total do not require payment.",
        ):
            create_payment_attempt(
                order=self.order,
                method=Payment.Method.PIX,
            )

        self.assertEqual(Payment.objects.count(), 0)

    def test_invalid_payment_method_is_rejected(self):
        with self.assertRaisesMessage(
            PaymentError,
            "Invalid payment method: boleto.",
        ):
            create_payment_attempt(
                order=self.order,
                method="boleto",
            )

        self.assertEqual(Payment.objects.count(), 0)
