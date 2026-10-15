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
    product_image = serializers.SerializerMethodField()
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

    def get_product_image(self, obj):
        images = list(
            obj.variant.product.images.all()
        )

        matching_images = [
            image
            for image in images
            if image.color_id == obj.variant.color_id
        ]

        generic_images = [
            image
            for image in images
            if image.color_id is None
        ]

        selected_image = (
            next(
                (
                    image
                    for image in matching_images
                    if image.is_primary
                ),
                None,
            )
            or (
                matching_images[0]
                if matching_images
                else None
            )
            or next(
                (
                    image
                    for image in generic_images
                    if image.is_primary
                ),
                None,
            )
            or (
                generic_images[0]
                if generic_images
                else None
            )
            or next(
                (
                    image
                    for image in images
                    if image.is_primary
                ),
                None,
            )
            or (
                images[0]
                if images
                else None
            )
        )

        if selected_image is None:
            return None

        image_url = selected_image.image.url
        request = self.context.get("request")

        if request is not None:
            return request.build_absolute_uri(
                image_url
            )

        return image_url

    class Meta:
        model = CartItem
        fields = (
            "id",
            "variant_id",
            "product_name",
            "product_slug",
            "product_image",
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
