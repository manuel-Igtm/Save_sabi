"""
Pytest configuration for Save Sabi tests.
"""

import os
import django
from django.conf import settings

# Set environment variables for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'save_sabi.settings')
os.environ.setdefault('USE_SQLITE', 'True')
os.environ.setdefault('USE_LOCAL_CACHE', 'True')

# Setup Django
django.setup()

import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create and return a test user."""
    from core.models import User
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def wallet(db, user):
    """Return the user's primary wallet."""
    from core.models import Wallet
    return Wallet.objects.get(owner=user, is_primary=True)
