from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint - returns 200 OK"""
    return JsonResponse({"status": "ok"})
