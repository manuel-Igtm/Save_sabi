"""
Django signals for the core app.

Handles automatic actions like creating default wallets and streaks.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import User, Wallet, SavingsStreak


@receiver(post_save, sender=User)
def create_default_wallet(sender, instance, created, **kwargs):
    """
    Create a default primary wallet when a new user is created.
    """
    if created:
        Wallet.objects.create(
            owner=instance,
            name='Primary Wallet',
            currency=instance.preferred_currency or settings.SAVE_SABI.get('DEFAULT_CURRENCY', 'KES'),
            is_primary=True,
            savings_ratio=settings.SAVE_SABI.get('DEFAULT_SPLIT_RATIO', (20, 80))[0]
        )


@receiver(post_save, sender=Wallet)
def create_savings_streak(sender, instance, created, **kwargs):
    """
    Create a SavingsStreak record when a new wallet is created.
    """
    if created:
        SavingsStreak.objects.get_or_create(wallet=instance)
