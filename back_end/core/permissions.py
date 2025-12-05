"""
Custom permissions for Save Sabi API.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    
    Assumes the model instance has an `owner` attribute or
    a `wallet.owner` attribute for related objects.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        # Check if object has direct owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # Check if object is related to a wallet with an owner
        if hasattr(obj, 'wallet'):
            return obj.wallet.owner == request.user
        
        return False


class IsWalletOwner(permissions.BasePermission):
    """
    Permission to check if user owns the wallet referenced in the request.
    """
    message = "You do not have permission to access this wallet."

    def has_permission(self, request, view):
        # For list/create views, we filter in the viewset
        return True

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsTransactionOwner(permissions.BasePermission):
    """
    Permission to check if user owns the transaction's wallet.
    """
    message = "You do not have permission to access this transaction."

    def has_object_permission(self, request, view, obj):
        return obj.wallet.owner == request.user


class IsGoalOwner(permissions.BasePermission):
    """
    Permission to check if user owns the goal's wallet.
    """
    message = "You do not have permission to access this goal."

    def has_object_permission(self, request, view, obj):
        return obj.wallet.owner == request.user


class IsNudgeOwner(permissions.BasePermission):
    """
    Permission to check if user owns the nudge's wallet.
    """
    message = "You do not have permission to access this nudge."

    def has_object_permission(self, request, view, obj):
        return obj.wallet.owner == request.user


class IsRuleOwner(permissions.BasePermission):
    """
    Permission to check if user owns the rule's wallet.
    """
    message = "You do not have permission to access this budget rule."

    def has_object_permission(self, request, view, obj):
        return obj.wallet.owner == request.user
