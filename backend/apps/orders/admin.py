from django.contrib import admin

from .models import Order, OrderItem, Payment, PaymentEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "variant",
        "product_name",
        "sku",
        "color_name",
        "size_name",
        "unit_price",
        "quantity",
        "total_price_display",
        "created_at",
    )
    autocomplete_fields = ("variant",)
    readonly_fields = (
        "total_price_display",
        "created_at",
    )
    show_change_link = True

    @admin.display(description="Total")
    def total_price_display(self, obj):
        if not obj.pk:
            return "-"
        return obj.total_price


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = (
        "method",
        "provider",
        "status",
        "amount",
        "external_id",
        "paid_at",
        "refunded_at",
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )
    show_change_link = True


class PaymentEventInline(admin.TabularInline):
    model = PaymentEvent
    extra = 0
    can_delete = False
    fields = (
        "provider",
        "event_id",
        "event_type",
        "external_payment_id",
        "external_status",
        "processed_at",
        "processing_error",
        "created_at",
    )
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "customer_name",
        "customer_email",
        "status",
        "payment_status",
        "items_count_display",
        "total_amount",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "public_id",
        "customer_name",
        "customer_email",
        "user__email",
        "shipping_postal_code",
        "shipping_street",
        "shipping_neighborhood",
        "shipping_city",
        "shipping_state",
        "items__sku",
        "items__product_name",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("user",)

    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    "public_id",
                    "user",
                    "customer_name",
                    "customer_email",
                )
            },
        ),
        (
            "Shipping address",
            {
                "fields": (
                    "shipping_postal_code",
                    "shipping_street",
                    "shipping_number",
                    "shipping_complement",
                    "shipping_neighborhood",
                    "shipping_city",
                    "shipping_state",
                    "shipping_country",
                )
            },
        ),
        (
            "Order",
            {
                "fields": (
                    "status",
                    "payment_status",
                    "items_count_display",
                    "notes",
                )
            },
        ),
        (
            "Amounts",
            {
                "fields": (
                    "subtotal",
                    "shipping_amount",
                    "discount_amount",
                    "total_amount",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "items_count_display",
    )
    date_hierarchy = "created_at"
    inlines = (
        OrderItemInline,
        PaymentInline,
    )

    @admin.display(description="Items")
    def items_count_display(self, obj):
        if not obj.pk:
            return 0
        return obj.items.count()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "method",
        "provider",
        "status",
        "amount",
        "external_id",
        "paid_at",
        "created_at",
    )
    list_filter = (
        "method",
        "provider",
        "status",
        "created_at",
        "paid_at",
        "refunded_at",
    )
    search_fields = (
        "external_id",
        "order__public_id",
        "order__customer_name",
        "order__customer_email",
    )
    autocomplete_fields = ("order",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = (
        PaymentEventInline,
    )


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "provider",
        "event_id",
        "event_type",
        "external_status",
        "external_payment_id",
        "processed_at",
        "created_at",
    )
    list_filter = (
        "provider",
        "external_status",
        "event_type",
        "processed_at",
        "created_at",
    )
    search_fields = (
        "event_id",
        "external_payment_id",
        "processing_error",
        "payment__external_id",
        "payment__order__public_id",
        "payment__order__customer_name",
        "payment__order__customer_email",
    )
    readonly_fields = (
        "payment",
        "provider",
        "event_id",
        "event_type",
        "external_payment_id",
        "external_status",
        "payload",
        "processed_at",
        "processing_error",
        "created_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Event",
            {
                "fields": (
                    "provider",
                    "event_id",
                    "event_type",
                    "external_status",
                    "external_payment_id",
                )
            },
        ),
        (
            "Processing",
            {
                "fields": (
                    "payment",
                    "processed_at",
                    "processing_error",
                )
            },
        ),
        (
            "Payload",
            {
                "fields": (
                    "payload",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "sku",
        "color_name",
        "size_name",
        "unit_price",
        "quantity",
        "total_price_display",
        "created_at",
    )
    list_filter = (
        "color_name",
        "size_name",
        "created_at",
    )
    search_fields = (
        "order__public_id",
        "order__customer_name",
        "order__customer_email",
        "product_name",
        "sku",
    )
    autocomplete_fields = (
        "order",
        "variant",
    )
    readonly_fields = (
        "created_at",
        "total_price_display",
    )

    @admin.display(description="Total")
    def total_price_display(self, obj):
        return obj.total_price
