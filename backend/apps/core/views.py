from django.db import DatabaseError, connection
from django.http import JsonResponse


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse(
            {"status": "unavailable"},
            status=503,
        )

    return JsonResponse(
        {"status": "ok"},
        status=200,
    )
