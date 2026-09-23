from rest_framework import serializers

from .models import (
    Category,
    Color,
    Product,
    ProductImage,
    ProductVariant,
    Size,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "name",
            "slug",
            "description",
        )


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = (
            "name",
            "slug",
            "hex_code",
        )


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = (
            "name",
            "slug",
        )


class ProductVariantSerializer(serializers.ModelSerializer):
    color = ColorSerializer(
        read_only=True,
    )
    size = SizeSerializer(
        read_only=True,
    )
    effective_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    is_in_stock = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "color",
            "size",
            "effective_price",
            "stock_quantity",
            "is_in_stock",
        )


class ProductImageSerializer(serializers.ModelSerializer):
    color = ColorSerializer(
        read_only=True,
    )

    class Meta:
        model = ProductImage
        fields = (
            "id",
            "image",
            "color",
            "alt_text",
            "sort_order",
            "is_primary",
        )


class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "short_description",
            "description",
            "base_price",
            "compare_at_price",
            "is_featured",
            "is_in_stock",
            "categories",
            "variants",
            "images",
            "created_at",
            "updated_at",
        )

    def get_categories(self, obj):
        categories = obj.categories.filter(
            is_active=True,
        )

        return CategorySerializer(
            categories,
            many=True,
            context=self.context,
        ).data

    def get_variants(self, obj):
        variants = (
            obj.variants
            .filter(
                is_active=True,
                color__is_active=True,
                size__is_active=True,
            )
            .select_related(
                "color",
                "size",
            )
        )

        return ProductVariantSerializer(
            variants,
            many=True,
            context=self.context,
        ).data

    def get_is_in_stock(self, obj):
        return obj.variants.filter(
            is_active=True,
            stock_quantity__gt=0,
            color__is_active=True,
            size__is_active=True,
        ).exists()
