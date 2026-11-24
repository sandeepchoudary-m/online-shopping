# Owner: Member 2, Customer classes and customer registration/login logic
"""
models/customer.py
==================
Demonstrates Object-Oriented Programming (CO5) with:
1. Class Hierarchy: Base class `Customer` and derived tiers (`StudentCustomer`, `PremiumCustomer`).
2. Polymorphism: Each tier overrides `discount_rate()` to award customer-specific member discounts
   (0% for Regular, 5% for Students, 10% for Premium members).
"""

from typing import Dict, Any


class Customer:
    """
    Base class representing a standard/regular retail customer.
    
    Attributes:
        customer_id (str): Unique customer ID (e.g., 'C001').
        name (str): Full name of the customer.
        email (str): Registered email address.
    """

    def __init__(self, customer_id: str, name: str, email: str):
        self.customer_id = str(customer_id).strip()
        self.name = str(name).strip()
        self.email = str(email).strip().lower()
        self.customer_type = "Regular"

    def discount_rate(self) -> float:
        """
        Base member discount rate.
        Returns:
            float: 0.0 (Regular customers get 0% membership discount).
        Subclasses override this polymorphically!
        """
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes customer profile for JSON/CSV storage."""
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "type": self.customer_type,
            "discount_rate": self.discount_rate(),
            "discount_percent": int(self.discount_rate() * 100)
        }

    def __str__(self) -> str:
        return f"[{self.customer_id}] {self.name} ({self.customer_type} Member - {int(self.discount_rate()*100)}% off)"


class StudentCustomer(Customer):
    """
    Subclass representing enrolled student members.
    
    Polymorphic behavior:
        Receives an additional 5% loyalty discount (0.05) on the bill.
    """

    def __init__(self, customer_id: str, name: str, email: str):
        super().__init__(customer_id, name, email)
        self.customer_type = "Student"

    def discount_rate(self) -> float:
        """Polymorphic override: 5% student discount."""
        return 0.05


class PremiumCustomer(Customer):
    """
    Subclass representing VIP/Premium loyalty club members.
    
    Polymorphic behavior:
        Receives an exclusive 10% loyalty discount (0.10) on the bill.
    """

    def __init__(self, customer_id: str, name: str, email: str):
        super().__init__(customer_id, name, email)
        self.customer_type = "Premium"

    def discount_rate(self) -> float:
        """Polymorphic override: 10% premium member discount."""
        return 0.10
