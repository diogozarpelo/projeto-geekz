from django.contrib import admin

from .models import (
    Category,
    Color,
    Product,
    ProductImage,
    ProductVariant,
    Size,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = (
        "sku",
        "color",
        "size",
        "price",
        "stock_quantity",
        "is_active",
    )
    autocomplete_fields = ("color", "size")
    show_change_link = True


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = (
        "image",
        "color",
        "alt_text",
        "sort_order",
        "is_primary",
    )
    autocomplete_fields = ("color",)
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "sort_order",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    ordering = ("sort_order", "name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("sort_order", "is_active")


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "hex_code",
        "sort_order",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "hex_code")
    ordering = ("sort_order", "name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("sort_order", "is_active")


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "sort_order",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("sort_order", "name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("sort_order", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "base_price",
        "compare_at_price",
        "is_featured",
        "is_active",
        "updated_at",
    )
    list_filter = (
        "is_active",
        "is_featured",
        "categories",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "name",
        "slug",
        "short_description",
        "description",
        "variants__sku",
    )
    ordering = ("-created_at",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("categories",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_featured", "is_active")
    date_hierarchy = "created_at"
    inlines = (
        ProductVariantInline,
        ProductImageInline,
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "color",
        "size",
        "display_price",
        "stock_quantity",
        "is_active",
    )
    list_filter = (
        "is_active",
        "color",
        "size",
    )
    search_fields = (
        "sku",
        "product__name",
        "product__slug",
    )
    autocomplete_fields = (
        "product",
        "color",
        "size",
    )
    list_editable = (
        "stock_quantity",
        "is_active",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Price")
    def display_price(self, obj):
        return obj.effective_price


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "color",
        "is_primary",
        "sort_order",
        "created_at",
    )
    list_filter = (
        "is_primary",
        "color",
        "created_at",
    )
    search_fields = (
        "product__name",
        "alt_text",
    )
    autocomplete_fields = (
        "product",
        "color",
    )
    list_editable = (
        "is_primary",
        "sort_order",
    )
    ordering = (
        "product",
        "sort_order",
        "id",
    )