from types import SimpleNamespace

from django.test import SimpleTestCase

from .serializers import CartItemSerializer


class CartItemImageSerializerTests(SimpleTestCase):
    def make_image(
        self,
        *,
        url,
        color_id=None,
        is_primary=False,
    ):
        return SimpleNamespace(
            color_id=color_id,
            is_primary=is_primary,
            image=SimpleNamespace(
                url=url,
            ),
        )

    def make_item(
        self,
        *,
        color_id,
        images,
    ):
        product = SimpleNamespace(
            images=SimpleNamespace(
                all=lambda: images,
            ),
        )

        variant = SimpleNamespace(
            color_id=color_id,
            product=product,
        )

        return SimpleNamespace(
            variant=variant,
        )

    def make_serializer(self):
        request = SimpleNamespace(
            build_absolute_uri=lambda url: (
                f"https://testserver{url}"
            ),
        )

        return CartItemSerializer(
            context={
                "request": request,
            },
        )

    def test_prefers_image_matching_variant_color(self):
        generic_image = self.make_image(
            url="/media/products/generic.webp",
            is_primary=True,
        )
        color_image = self.make_image(
            url="/media/products/blue.webp",
            color_id=2,
        )

        item = self.make_item(
            color_id=2,
            images=[
                generic_image,
                color_image,
            ],
        )

        serializer = self.make_serializer()

        self.assertEqual(
            serializer.get_product_image(item),
            "https://testserver/media/products/blue.webp",
        )

    def test_uses_generic_image_when_color_has_no_image(self):
        generic_image = self.make_image(
            url="/media/products/generic.webp",
            is_primary=True,
        )

        item = self.make_item(
            color_id=5,
            images=[
                generic_image,
            ],
        )

        serializer = self.make_serializer()

        self.assertEqual(
            serializer.get_product_image(item),
            "https://testserver/media/products/generic.webp",
        )

    def test_returns_none_when_product_has_no_images(self):
        item = self.make_item(
            color_id=1,
            images=[],
        )

        serializer = self.make_serializer()

        self.assertIsNone(
            serializer.get_product_image(item)
        )
