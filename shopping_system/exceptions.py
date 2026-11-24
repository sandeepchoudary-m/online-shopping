# Owner: Member 1, Product classes and custom exceptions
"""
exceptions.py
=============
Custom exception hierarchy for the Online Shopping Management System (ShopEase).

Why custom exceptions?
In Python, using specific custom exceptions derived from a base class allows us
to cleanly catch and handle application-specific errors without catching unrelated
Python system errors (like NameError or SyntaxError).

When any of these exceptions are raised in our business logic (e.g., in models or services),
Flask's error handlers intercept them and return user-friendly HTTP 400 responses.
"""


class ShoppingError(Exception):
    """
    Base exception class for all errors in the Shopping Management System.
    Inheriting from Python's built-in Exception class allows all child exceptions
    to be caught under one single parent type: `except ShoppingError:`.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class InvalidProductError(ShoppingError):
    """
    Raised when a requested product ID does not exist in the catalogue,
    or when a product record is structurally invalid.
    """
    pass


class InsufficientStockError(ShoppingError):
    """
    Raised when a customer attempts to purchase or add more units of a product
    than are currently available in the inventory.
    """
    pass


class InvalidQuantityError(ShoppingError):
    """
    Raised when an invalid quantity value is provided (such as non-numeric strings,
    zero, negative numbers, or non-integer floating point numbers).
    """
    pass


class EmptyCartError(ShoppingError):
    """
    Raised when a customer attempts to proceed to checkout with no items in their cart.
    """
    pass


class InvalidCustomerError(ShoppingError):
    """
    Raised when a customer ID cannot be found or customer profile data is invalid.
    """
    pass


class DataFileError(ShoppingError):
    """
    Raised when a storage file (JSON or CSV) cannot be found, is corrupted,
    contains invalid records (e.g. negative price or duplicate ID), has an
    unsupported file extension, or cannot be written due to file permissions.
    """
    pass
