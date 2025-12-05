# Save Sabi Django Project
# Smart savings platform implementing the Hara Hachi Bu 80/20 principle

from .celery import app as celery_app

__all__ = ('celery_app',)
