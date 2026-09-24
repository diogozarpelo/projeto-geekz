import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    customer_name = models.CharField(max_length=160)
    customer_email = models.EmailField()

    shipping_postal_code = models.CharField(
        max_length=20,
        default="",
    )
    shipping_street = models.CharField(
        max_length=180,
        default="",
    )
    shipping_number = models.CharField(
        max_length=30,
        default="",
    )
    shipping_complement = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    shipping_neighborhood = models.CharField(
        max_length=120,
        default="",
    )
    shipping_city = models.CharField(
        max_length=120,
        default="",
    )
    shipping_state = models.CharField(
        max_length=80,
        default="",
    )
    shipping_country = models.CharField(
        max_length=80,
        default="BR",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    shipping_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("status", "created_at"),
                name="order_status_created_idx",
            ),
            models.Index(
                fields=("payment_status", "created_at"),
                name="order_payment_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(subtotal__gte=0)
                    & models.Q(shipping_amount__gte=0)
                    & models.Q(discount_amount__gte=0)
                    & models.Q(total_amount__gte=0)
                ),
                name="order_amounts_gte_0",
            ),
        ]

    def __str__(self):
        return f"Order {self.public_id} - {self.customer_email}"


class Payment(models.Model):
    class Method(models.TextChoices):
        PIX = "pix", "Pix"
        CREDIT_CARD = "credit_card", "Credit card"

    class Provider(models.TextChoices):
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    method = models.CharField(
        max_length=30,
        choices=Method.choices,
    )
    provider = models.CharField(
        max_length=40,
        choices=Provider.choices,
        default=Provider.MERCADO_PAGO,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    external_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    provider_order_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    idempotency_key = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )
    provider_data = models.JSONField(
        default=dict,
        blank=True,
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("status", "created_at"),
                name="payment_status_created_idx",
            ),
            models.Index(
                fields=("provider_order_id",),
                name="payment_provider_order_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="payment_amount_gte_0",
            ),
            models.UniqueConstraint(
                fields=("provider", "external_id"),
                condition=~models.Q(external_id=""),
                name="unique_provider_external_payment",
            ),
            models.UniqueConstraint(
                fields=("provider", "provider_order_id"),
                condition=~models.Q(provider_order_id=""),
                name="unique_provider_order_payment",
            ),
            models.UniqueConstraint(
                fields=("idempotency_key",),
                condition=~models.Q(idempotency_key=""),
                name="unique_payment_idempotency_key",
            ),
        ]

    def __str__(self):
        return (
            f"Payment {self.id} - "
            f"{self.order.public_id} - "
            f"{self.status}"
        )


class PaymentEvent(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    provider = models.CharField(
        max_length=40,
        choices=Payment.Provider.choices,
        default=Payment.Provider.MERCADO_PAGO,
    )
    event_id = models.CharField(
        max_length=160,
        blank=True,
        default="",
    )
    event_type = models.CharField(
        max_length=80,
        blank=True,
        default="",
    )
    external_payment_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    external_status = models.CharField(
        max_length=50,
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    processing_error = models.TextField(
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("external_status", "created_at"),
                name="payment_event_status_idx",
            ),
            models.Index(
                fields=("external_payment_id",),
                name="payment_event_external_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "event_id"),
                condition=~models.Q(event_id=""),
                name="unique_provider_payment_event",
            ),
        ]

    def __str__(self):
        return (
            f"Payment event {self.id} - "
            f"{self.provider} - "
            f"{self.external_status}"
        )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
    )

    product_name = models.CharField(max_length=160)
    sku = models.CharField(max_length=80)
    color_name = models.CharField(max_length=50)
    size_name = models.CharField(max_length=20)

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="order_item_unit_price_gte_0",
            ),
        ]

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} - {self.sku} x {self.quantity}"
