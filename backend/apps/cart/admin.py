from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = (
        "variant",
        "quantity",
        "unit_price_display",
        "total_price_display",
        "created_at",
    )
    autocomplete_fields = ("variant",)
    readonly_fields = (
        "unit_price_display",
        "total_price_display",
        "created_at",
    )

    @admin.display(description="Unit price")
    def unit_price_display(self, obj):
        if not obj.pk:
            return "-"
        return obj.unit_price

    @admin.display(description="Total")
    def total_price_display(self, obj):
        if not obj.pk:
            return "-"
        return obj.total_price


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "user",
        "status",
        "total_items_display",
        "subtotal_display",
        "updated_at",
    )
    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "public_id",
        "user__email",
    )
    ordering = ("-updated_at",)
    raw_id_fields = ("user",)
    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "total_items_display",
        "subtotal_display",
    )
    date_hierarchy = "created_at"
    inlines = (CartItemInline,)

    @admin.display(description="Items")
    def total_items_display(self, obj):
        return obj.total_items

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        return obj.subtotal


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cart",
        "variant",
        "quantity",
        "unit_price_display",
        "total_price_display",
        "updated_at",
    )
    list_filter = (
        "variant__color",
        "variant__size",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "cart__public_id",
        "cart__user__email",
        "variant__sku",
        "variant__product__name",
    )
    autocomplete_fields = (
        "cart",
        "variant",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "unit_price_display",
        "total_price_display",
    )

    @admin.display(description="Unit price")
    def unit_price_display(self, obj):
        return obj.unit_price

    @admin.display(description="Total")
    def total_price_display(self, obj):
        return obj.total_price