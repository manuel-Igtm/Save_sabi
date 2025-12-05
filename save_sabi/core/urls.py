"""
URL Configuration for the core app.

This module defines all API endpoints for Save Sabi:
- Authentication: /auth/
- Wallets: /wallets/
- Transactions: /transactions/
- Summaries: /summaries/
- Goals: /goals/
- Budget Rules: /rules/
- Nudges: /nudges/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Auth views
    RegisterView, LoginView, LogoutView, UserProfileView, ChangePasswordView,
    # Resource views
    WalletViewSet, TransactionViewSet, SummaryView,
    GoalViewSet, BudgetRuleViewSet, NudgeViewSet, NudgeAcknowledgeView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'rules', BudgetRuleViewSet, basename='rule')
router.register(r'nudges', NudgeViewSet, basename='nudge')

# Auth URLs
auth_urls = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]

urlpatterns = [
    # Auth endpoints
    path('auth/', include((auth_urls, 'auth'))),
    
    # Summary endpoint (not a ViewSet)
    path('summaries/', SummaryView.as_view(), name='summaries'),
    
    # Nudge acknowledge endpoint
    path('nudges/acknowledge/', NudgeAcknowledgeView.as_view(), name='nudge-acknowledge'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
