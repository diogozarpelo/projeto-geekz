from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(
        source="variant.id",
        read_only=True,
    )
    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True,
    )
    product_slug = serializers.CharField(
        source="variant.product.slug",
        read_only=True,
    )
    sku = serializers.CharField(
        source="variant.sku",
        read_only=True,
    )
    color_name = serializers.CharField(
        source="variant.color.name",
        read_only=True,
    )
    color_slug = serializers.CharField(
        source="variant.color.slug",
        read_only=True,
    )
    color_hex = serializers.CharField(
        source="variant.color.hex_code",
        read_only=True,
    )
    size_name = serializers.CharField(
        source="variant.size.name",
        read_only=True,
    )
    size_slug = serializers.CharField(
        source="variant.size.slug",
        read_only=True,
    )
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    available_stock = serializers.IntegerField(
        source="variant.stock_quantity",
        read_only=True,
    )
    is_in_stock = serializers.BooleanField(
        source="variant.is_in_stock",
        read_only=True,
    )

    class Meta:
        model = CartItem
        fields = (
            "id",
            "variant_id",
            "product_name",
            "product_slug",
            "sku",
            "color_name",
            "color_slug",
            "color_hex",
            "size_name",
            "size_slug",
            "unit_price",
            "quantity",
            "total_price",
            "available_stock",
            "is_in_stock",
        )
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(
        many=True,
        read_only=True,
    )
    total_items = serializers.IntegerField(
        read_only=True,
    )
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Cart
        fields = (
            "public_id",
            "status",
            "total_items",
            "subtotal",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(
        min_value=1,
    )
    quantity = serializers.IntegerField(
        min_value=1,
        required=False,
        default=1,
    )


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
    )
