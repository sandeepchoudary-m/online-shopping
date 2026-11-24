# Owner: Member 1, Product classes (inheritance + polymorphism) and custom exceptions
"""
models/product.py
=================
Demonstrates Object-Oriented Programming (CO5) with:
1. Class Hierarchy: Base class `Product` and derived subclasses (`Electronics`, `Grocery`, `Clothing`).
2. Constructor Chaining: Child classes call `super().__init__(...)` to reuse base attributes.
3. Polymorphism: Each subclass overrides `discount_rate()` and `is_sellable()` to provide
   domain-specific behavior without the caller needing `if-elif` type checks.
"""

from datetime import date, datetime
from typing import List, Dict, Any


class Product:
    """
    Base class representing a generic store product.
    
    Attributes:
        product_id (str): Unique alphanumeric identifier (e.g., 'P101').
        name (str): Human-readable product name.
        category (str): General category name (e.g., 'General', 'Electronics').
        price (float): Selling price in Rupees (Rs.).
        stock (int): Available inventory count in units.
        keywords (list): Search keywords for easy item discovery.
    """

    def __init__(self, product_id: str, name: str, category: str, price: float, stock: int, keywords=None):
        self.product_id = str(product_id).strip()
        self.name = str(name).strip()
        self.category = str(category).strip()
        self.price = float(price)
        self.stock = int(stock)

        # Convert keywords to a clean list of lowercase strings
        if keywords is None:
            self.keywords: List[str] = []
        elif isinstance(keywords, str):
            # Split comma-separated string if provided
            self.keywords = [k.strip().lower() for k in keywords.split(",") if k.strip()]
        else:
            self.keywords = [str(k).strip().lower() for k in keywords if str(k).strip()]

    def discount_rate(self) -> float:
        """
        Base discount rate for a standard product.
        Returns:
            float: 0.0 (0% discount by default).
        Subclasses override this to implement polymorphism!
        """
        return 0.0

    def is_sellable(self) -> bool:
        """
        Determines whether the product is currently eligible for sale.
        A standard product is sellable as long as it has stock > 0.
        """
        return self.stock > 0

    def get_extra_details(self) -> Dict[str, Any]:
        """
        Returns extra subclass-specific details as a dictionary.
        Base class returns an empty dictionary; subclasses override this.
        """
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the product object to a dictionary for JSON/CSV storage.
        """
        data = {
            "type": self.__class__.__name__,
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "price": round(self.price, 2),
            "stock": self.stock,
            "keywords": self.keywords,
            "discount_rate": self.discount_rate(),
            "is_sellable": self.is_sellable(),
            "details": self.get_extra_details()
        }
        # Merge extra fields for flat serialization
        data.update(self.get_extra_details())
        return data

    def __str__(self) -> str:
        """User-friendly string representation of the product."""
        return f"[{self.product_id}] {self.name} ({self.category}) - Rs. {self.price:.2f} (Stock: {self.stock})"


class Electronics(Product):
    """
    Subclass representing Electronic gadgets and appliances.
    
    Extra attribute:
        warranty_months (int): Duration of manufacturer warranty in months.
    
    Polymorphic behavior:
        Offers a flat 5% discount (0.05).
    """

    def __init__(self, product_id: str, name: str, category: str, price: float, stock: int,
                 keywords=None, warranty_months: int = 12):
        # Call parent constructor to initialize shared product attributes
        super().__init__(product_id, name, category, price, stock, keywords)
        self.warranty_months = int(warranty_months)

    def discount_rate(self) -> float:
        """Polymorphic override: Electronics receive a 5% discount."""
        return 0.05

    def get_extra_details(self) -> Dict[str, Any]:
        return {"warranty_months": self.warranty_months}


class Grocery(Product):
    """
    Subclass representing perishable grocery and food items.
    
    Extra attribute:
        expiry_date (str): Expiration date string in 'YYYY-MM-DD' format.
        
    Polymorphic behavior:
        1. If already expired: Not sellable (`is_sellable()` returns False).
        2. If expiring within 7 days: 30% discount (0.30) to clear perishable stock!
        3. If fresh (> 7 days remaining): 0% discount.
    """

    def __init__(self, product_id: str, name: str, category: str, price: float, stock: int,
                 keywords=None, expiry_date: str = "2026-12-31"):
        super().__init__(product_id, name, category, price, stock, keywords)
        self.expiry_date = str(expiry_date).strip()

    def parse_expiry(self) -> date:
        """Safely parses the expiry_date string into a datetime.date object."""
        try:
            return date.fromisoformat(self.expiry_date)
        except (ValueError, TypeError):
            # Fallback parsing if string contains unexpected formatting
            return datetime.strptime(self.expiry_date, "%Y-%m-%d").date()

    def days_until_expiry(self) -> int:
        """Calculates days left until expiration relative to current date."""
        today = date.today()
        exp_date = self.parse_expiry()
        return (exp_date - today).days

    def is_expired(self) -> bool:
        """Returns True if the item is past its expiration date."""
        return self.days_until_expiry() < 0

    def is_sellable(self) -> bool:
        """
        Polymorphic override:
        Grocery items CANNOT be sold if they are expired, even if stock exists!
        """
        if self.is_expired():
            return False
        return self.stock > 0

    def discount_rate(self) -> float:
        """
        Polymorphic override:
        Perishable clearance discount: 30% off if expiring within 7 days (and not expired).
        """
        days_left = self.days_until_expiry()
        if 0 <= days_left <= 7:
            return 0.30  # 30% discount for quick clearance
        return 0.0

    def get_extra_details(self) -> Dict[str, Any]:
        return {
            "expiry_date": self.expiry_date,
            "days_left": self.days_until_expiry(),
            "is_expired": self.is_expired()
        }


class Clothing(Product):
    """
    Subclass representing apparel and garments.
    
    Extra attribute:
        size (str): Garment size (e.g., 'S', 'M', 'L', 'XL', 'Free Size').
        
    Polymorphic behavior:
        Offers a seasonal 15% discount (0.15).
    """

    def __init__(self, product_id: str, name: str, category: str, price: float, stock: int,
                 keywords=None, size: str = "M"):
        super().__init__(product_id, name, category, price, stock, keywords)
        self.size = str(size).strip().upper()

    def discount_rate(self) -> float:
        """Polymorphic override: Clothing receives a 15% discount."""
        return 0.15

    def get_extra_details(self) -> Dict[str, Any]:
        return {"size": self.size}
