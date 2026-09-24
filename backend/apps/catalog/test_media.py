from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse
import uuid

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Product, ProductImage


GIF_BYTES = (
    b"GIF89a"
    b"\x01\x00\x01\x00"
    b"\x80\x00\x00"
    b"\x00\x00\x00"
    b"\xff\xff\xff"
    b"!\xf9\x04\x01\x00\x00\x00\x00"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00"
    b"\x02\x02D\x01\x00;"
)


class CatalogMediaTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Camiseta Midia API",
            slug="camiseta-midia-api",
            description="Produto para teste de imagem.",
            base_price=Decimal("89.90"),
            is_active=True,
        )

        filename = (
            f"catalog-media-{uuid.uuid4().hex}.gif"
        )

        upload = SimpleUploadedFile(
            filename,
            GIF_BYTES,
            content_type="image/gif",
        )

        self.product_image = ProductImage.objects.create(
            product=self.product,
            image=upload,
            alt_text="Imagem de teste do catalogo",
            is_primary=True,
        )

        self.saved_path = Path(
            self.product_image.image.path
        )

    def tearDown(self):
        if self.saved_path.exists():
            self.saved_path.unlink()

        media_root = Path(
            settings.MEDIA_ROOT
        ).resolve()

        parent = self.saved_path.parent.resolve()

        while (
            parent != media_root
            and media_root in parent.parents
        ):
            try:
                parent.rmdir()
            except OSError:
                break

            parent = parent.parent

    def product_detail_response(self):
        return self.client.get(
            reverse(
                "catalog:product-detail",
                kwargs={
                    "slug": self.product.slug,
                },
            )
        )

    def test_product_api_returns_media_url(self):
        response = self.product_detail_response()

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            len(response.data["images"]),
            1,
        )

        image_url = response.data["images"][0][
            "image"
        ]

        image_path = urlparse(
            image_url
        ).path

        self.assertTrue(
            image_path.startswith(
                settings.MEDIA_URL
            )
        )
        self.assertIn(
            "/products/",
            image_path,
        )

    def test_product_image_is_saved_inside_media_root(self):
        media_root = Path(
            settings.MEDIA_ROOT
        ).resolve()

        saved_path = self.saved_path.resolve()

        self.assertTrue(
            saved_path.exists(),
        )
        self.assertTrue(
            saved_path.is_file(),
        )
        self.assertIn(
            media_root,
            saved_path.parents,
        )
        self.assertEqual(
            saved_path.read_bytes(),
            GIF_BYTES,
        )
