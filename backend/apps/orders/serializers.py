from decimal import Decimal

from rest_framework import serializers

from .models import Order, OrderItem, Payment


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product_name",
            "sku",
            "color_name",
            "size_name",
            "unit_price",
            "quantity",
            "total_price",
        )


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "method",
            "provider",
            "status",
            "amount",
            "external_id",
            "paid_at",
            "refunded_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )
    payments = PaymentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "public_id",
            "customer_name",
            "customer_email",
            "shipping_postal_code",
            "shipping_street",
            "shipping_number",
            "shipping_complement",
            "shipping_neighborhood",
            "shipping_city",
            "shipping_state",
            "shipping_country",
            "status",
            "payment_status",
            "subtotal",
            "shipping_amount",
            "discount_amount",
            "total_amount",
            "notes",
            "items",
            "payments",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    cart_public_id = serializers.UUIDField()

    customer_name = serializers.CharField(
        max_length=160,
    )
    customer_email = serializers.EmailField()

    shipping_postal_code = serializers.CharField(
        max_length=20,
    )
    shipping_street = serializers.CharField(
        max_length=180,
    )
    shipping_number = serializers.CharField(
        max_length=30,
    )
    shipping_complement = serializers.CharField(
        max_length=120,
        allow_blank=True,
        required=False,
        default="",
    )
    shipping_neighborhood = serializers.CharField(
        max_length=120,
    )
    shipping_city = serializers.CharField(
        max_length=120,
    )
    shipping_state = serializers.CharField(
        max_length=80,
    )
    shipping_country = serializers.CharField(
        max_length=80,
        required=False,
        default="BR",
    )

    shipping_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        default=Decimal("0.00"),
    )
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        default=Decimal("0.00"),
    )

    notes = serializers.CharField(
        allow_blank=True,
        required=False,
        default="",
    )


class PaymentAttemptSerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=Payment.Method.choices,
    )
