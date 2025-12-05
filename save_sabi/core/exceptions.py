"""
Custom exceptions and exception handler for Save Sabi API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class SaveSabiException(Exception):
    """Base exception for Save Sabi application."""
    default_message = "An error occurred"
    default_code = "error"

    def __init__(self, message=None, code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class InsufficientBalanceError(SaveSabiException):
    """Raised when wallet balance is insufficient for a transaction."""
    default_message = "Insufficient balance for this transaction"
    default_code = "insufficient_balance"


class InvalidTransactionError(SaveSabiException):
    """Raised when a transaction is invalid."""
    default_message = "Invalid transaction"
    default_code = "invalid_transaction"


class WalletNotFoundError(SaveSabiException):
    """Raised when a wallet is not found."""
    default_message = "Wallet not found"
    default_code = "wallet_not_found"


class GoalNotFoundError(SaveSabiException):
    """Raised when a goal is not found."""
    default_message = "Goal not found"
    default_code = "goal_not_found"


class RuleNotFoundError(SaveSabiException):
    """Raised when a budget rule is not found."""
    default_message = "Budget rule not found"
    default_code = "rule_not_found"


class InvalidSplitRatioError(SaveSabiException):
    """Raised when split ratio is invalid."""
    default_message = "Split ratio must be between 1 and 99"
    default_code = "invalid_split_ratio"


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    
    Handles SaveSabiException and provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response data
        response.data = {
            'error': True,
            'code': getattr(exc, 'default_detail', 'error'),
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'details': response.data if isinstance(response.data, dict) else {'errors': response.data}
        }
        return response

    # Handle SaveSabiException
    if isinstance(exc, SaveSabiException):
        logger.warning(f"SaveSabiException: {exc.code} - {exc.message}", extra={
            'code': exc.code,
            'details': exc.details
        })
        return Response({
            'error': True,
            'code': exc.code,
            'message': exc.message,
            'details': exc.details
        }, status=status.HTTP_400_BAD_REQUEST)

    # Handle unexpected exceptions
    if isinstance(exc, Exception):
        logger.exception(f"Unexpected error: {str(exc)}")
        return Response({
            'error': True,
            'code': 'internal_error',
            'message': 'An unexpected error occurred',
            'details': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
