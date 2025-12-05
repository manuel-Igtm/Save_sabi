"""
Celery configuration for Save Sabi project.

This module sets up Celery for background task processing,
including nudge delivery and periodic summary calculations.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'save_sabi.settings')

app = Celery('save_sabi')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'evaluate-daily-rules': {
        'task': 'core.tasks.evaluate_all_daily_rules',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-nudges': {
        'task': 'core.tasks.cleanup_old_nudges',
        'schedule': 86400.0,  # Every 24 hours
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
