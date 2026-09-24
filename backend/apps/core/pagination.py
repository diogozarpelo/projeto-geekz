from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class CatalogPagination(PageNumberPagination):
    page_size = settings.CATALOG_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = settings.API_MAX_PAGE_SIZE


class OrderHistoryPagination(PageNumberPagination):
    page_size = settings.ORDER_HISTORY_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = settings.API_MAX_PAGE_SIZE
