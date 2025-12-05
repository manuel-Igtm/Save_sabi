"""
URL configuration for Save Sabi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from datetime import datetime


def health_check(request):
    """
    Health check endpoint for Cloud Run and load balancers.
    Returns status of database and cache connections.
    """
    health_status = {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'database': 'ok',
        'cache': 'ok',
    }
    status_code = 200

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as e:
        health_status['database'] = 'error'
        health_status['database_error'] = str(e)
        health_status['status'] = 'degraded'
        status_code = 503

    # Check cache connection
    try:
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        if cache_result != 'ok':
            raise Exception('Cache read/write failed')
    except Exception as e:
        health_status['cache'] = 'error'
        health_status['cache_error'] = str(e)
        # Cache failure is non-critical, keep status as ok if DB is fine
        if health_status['database'] == 'ok':
            health_status['status'] = 'ok'

    return JsonResponse(health_status, status=status_code)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', health_check, name='health_check'),
    path('api/v1/', include('core.urls')),
]
