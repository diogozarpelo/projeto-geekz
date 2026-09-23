from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from .models import (
    Category,
    Color,
    Product,
    ProductVariant,
    Size,
)


class CatalogAPITests(APITestCase):
    def setUp(self):
        self.games = Category.objects.create(
            name="Games API",
            slug="games-api",
            description="Categoria de games para testes.",
            is_active=True,
            sort_order=1,
        )

        self.animes = Category.objects.create(
            name="Animes API",
            slug="animes-api",
            description="Categoria de animes para testes.",
            is_active=True,
            sort_order=2,
        )

        self.inactive_category = Category.objects.create(
            name="Categoria Inativa API",
            slug="categoria-inativa-api",
            is_active=False,
            sort_order=3,
        )

        self.black = Color.objects.create(
            name="Preto Catalog API",
            slug="preto-catalog-api",
            hex_code="#000000",
            is_active=True,
        )

        self.white = Color.objects.create(
            name="Branco Catalog API",
            slug="branco-catalog-api",
            hex_code="#FFFFFF",
            is_active=True,
        )

        self.inactive_color = Color.objects.create(
            name="Cor Inativa Catalog API",
            slug="cor-inativa-catalog-api",
            hex_code="#123456",
            is_active=False,
        )

        self.size_m = Size.objects.create(
            name="M Catalog API",
            slug="m-catalog-api",
            is_active=True,
        )

        self.size_g = Size.objects.create(
            name="G Catalog API",
            slug="g-catalog-api",
            is_active=True,
        )

        self.inactive_size = Size.objects.create(
            name="X Catalog API",
            slug="x-catalog-api",
            is_active=False,
        )

        self.featured_product = Product.objects.create(
            name="Camiseta Zelda API",
            slug="camiseta-zelda-api",
            short_description="Camiseta inspirada em aventura.",
            description="Produto de Games usado na API.",
            base_price=Decimal("89.90"),
            compare_at_price=Decimal("109.90"),
            is_active=True,
            is_featured=True,
        )
        self.featured_product.categories.add(
            self.games,
            self.inactive_category,
        )

        self.anime_product = Product.objects.create(
            name="Camiseta Anime API",
            slug="camiseta-anime-api",
            short_description="Camiseta de anime.",
            description="Produto de Animes usado na API.",
            base_price=Decimal("79.90"),
            is_active=True,
            is_featured=False,
        )
        self.anime_product.categories.add(
            self.animes,
        )

        self.inactive_product = Product.objects.create(
            name="Produto Inativo API",
            slug="produto-inativo-api",
            description="Produto que nao deve aparecer.",
            base_price=Decimal("69.90"),
            is_active=False,
        )
        self.inactive_product.categories.add(
            self.games,
        )

        self.featured_variant = ProductVariant.objects.create(
            product=self.featured_product,
            color=self.black,
            size=self.size_m,
            sku="CATALOG-API-ZELDA-M",
            price=Decimal("94.90"),
            stock_quantity=5,
            is_active=True,
        )

        ProductVariant.objects.create(
            product=self.featured_product,
            color=self.white,
            size=self.size_g,
            sku="CATALOG-API-ZELDA-G",
            stock_quantity=0,
            is_active=True,
        )

        ProductVariant.objects.create(
            product=self.featured_product,
            color=self.inactive_color,
            size=self.inactive_size,
            sku="CATALOG-API-INACTIVE-VARIANT",
            stock_quantity=10,
            is_active=True,
        )

        ProductVariant.objects.create(
            product=self.anime_product,
            color=self.black,
            size=self.size_m,
            sku="CATALOG-API-ANIME-M",
            stock_quantity=0,
            is_active=True,
        )

    def test_category_list_is_public_and_only_returns_active_categories(self):
        response = self.client.get(
            reverse("catalog:category-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        slugs = {
            item["slug"]
            for item in response.data
        }

        self.assertIn(
            self.games.slug,
            slugs,
        )
        self.assertIn(
            self.animes.slug,
            slugs,
        )
        self.assertNotIn(
            self.inactive_category.slug,
            slugs,
        )

    def test_product_list_is_public_and_only_returns_active_products(self):
        response = self.client.get(
            reverse("catalog:product-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        slugs = {
            item["slug"]
            for item in response.data
        }

        self.assertIn(
            self.featured_product.slug,
            slugs,
        )
        self.assertIn(
            self.anime_product.slug,
            slugs,
        )
        self.assertNotIn(
            self.inactive_product.slug,
            slugs,
        )

    def test_product_detail_returns_product_by_slug(self):
        response = self.client.get(
            reverse(
                "catalog:product-detail",
                kwargs={
                    "slug": self.featured_product.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["slug"],
            self.featured_product.slug,
        )
        self.assertEqual(
            response.data["base_price"],
            "89.90",
        )
        self.assertEqual(
            response.data["compare_at_price"],
            "109.90",
        )
        self.assertTrue(
            response.data["is_in_stock"],
        )

    def test_inactive_product_detail_returns_not_found(self):
        response = self.client.get(
            reverse(
                "catalog:product-detail",
                kwargs={
                    "slug": self.inactive_product.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_product_serializer_hides_inactive_catalog_options(self):
        response = self.client.get(
            reverse(
                "catalog:product-detail",
                kwargs={
                    "slug": self.featured_product.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        category_slugs = {
            item["slug"]
            for item in response.data["categories"]
        }

        variant_skus = {
            item["sku"]
            for item in response.data["variants"]
        }

        self.assertIn(
            self.games.slug,
            category_slugs,
        )
        self.assertNotIn(
            self.inactive_category.slug,
            category_slugs,
        )
        self.assertIn(
            self.featured_variant.sku,
            variant_skus,
        )
        self.assertNotIn(
            "CATALOG-API-INACTIVE-VARIANT",
            variant_skus,
        )

    def test_product_list_can_filter_by_category(self):
        response = self.client.get(
            reverse("catalog:product-list"),
            {
                "category": self.games.slug,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        slugs = [
            item["slug"]
            for item in response.data
        ]

        self.assertEqual(
            slugs,
            [self.featured_product.slug],
        )

    def test_product_list_can_search_products(self):
        response = self.client.get(
            reverse("catalog:product-list"),
            {
                "search": "Zelda",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        slugs = {
            item["slug"]
            for item in response.data
        }

        self.assertEqual(
            slugs,
            {self.featured_product.slug},
        )

    def test_product_list_can_search_by_sku(self):
        response = self.client.get(
            reverse("catalog:product-list"),
            {
                "search": "CATALOG-API-ZELDA-M",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            len(response.data),
            1,
        )
        self.assertEqual(
            response.data[0]["slug"],
            self.featured_product.slug,
        )

    def test_product_list_can_filter_featured_products(self):
        response = self.client.get(
            reverse("catalog:product-list"),
            {
                "featured": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        slugs = {
            item["slug"]
            for item in response.data
        }

        self.assertEqual(
            slugs,
            {self.featured_product.slug},
        )

    def test_product_list_can_filter_products_in_stock(self):
        response = self.client.get(
            reverse("catalog:product-list"),
            {
                "in_stock": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        slugs = {
            item["slug"]
            for item in response.data
        }

        self.assertEqual(
            slugs,
            {self.featured_product.slug},
        )

    def test_invalid_boolean_filter_returns_bad_request(self):
        response = self.client.get(
            reverse("catalog:product-list"),
            {
                "featured": "talvez",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertIn(
            "featured",
            response.data,
        )
