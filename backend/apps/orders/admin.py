from django.contrib import admin

from .models import Order, OrderItem


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
    inlines = (OrderItemInline,)

    @admin.display(description="Items")
    def items_count_display(self, obj):
        if not obj.pk:
            return 0
        return obj.items.count()


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
