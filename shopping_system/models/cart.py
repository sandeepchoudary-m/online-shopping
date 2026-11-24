# Owner: Member 4, Shopping cart (validation, stock checks)
"""
models/cart.py
==============
Demonstrates Data Structures and String/Numeric Operations (CO3):
1. Dictionary: Internal storage `self.items = {product_id: quantity}` for O(1) lookups.
2. List of Tuples: `lines(catalogue)` returns `[(product, quantity, line_total), ...]`
   for immutable, structured line-item presentation.
3. Strict validation of quantities (rejecting zero, negatives, floats, non-numeric strings)
   and stock enforcement before updating state.
"""

from typing import Dict, List, Tuple, Any, Optional
from exceptions import InvalidQuantityError, InvalidProductError, InsufficientStockError, ShoppingError


class ShoppingCart:
    """
    Manages customer cart items, item quantities, and inventory stock checks.
    
    Attributes:
        items (dict): Maps product_id (str) to quantity (int).
    """

    def __init__(self):
        # Dictionary structure: { product_id: quantity }
        self.items: Dict[str, int] = {}

    def _validate_quantity(self, qty: Any) -> int:
        """
        Validates that a quantity is strictly a positive whole integer.
        Rejects:
            - Floats / Decimals like 1.5
            - Non-numeric strings like "abc"
            - Negative numbers like -3
            - Zero 0
            - Booleans (True/False)
        Returns:
            int: The sanitized integer quantity.
        Raises:
            InvalidQuantityError: If validation fails.
        """
        # Reject booleans (in Python, bool is a subclass of int: isinstance(True, int) is True)
        if isinstance(qty, bool):
            raise InvalidQuantityError("Quantity must be a positive integer, not a boolean value.")

        # Reject floating point numbers (e.g. 1.5, 2.0)
        if isinstance(qty, float):
            raise InvalidQuantityError(f"Quantity must be a whole number, got decimal: {qty}")

        # If passed as string, strip whitespace and check if purely digits
        if isinstance(qty, str):
            clean_str = qty.strip()
            if not clean_str.isdigit():
                raise InvalidQuantityError(
                    f"Quantity must be a valid positive integer, received: '{qty}'"
                )
            int_qty = int(clean_str)
        elif isinstance(qty, int):
            int_qty = qty
        else:
            raise InvalidQuantityError(f"Unsupported quantity type: {type(qty).__name__}")

        # Quantity must be strictly greater than zero
        if int_qty <= 0:
            raise InvalidQuantityError(
                f"Quantity must be greater than zero (positive whole number), got: {int_qty}"
            )

        return int_qty

    def add(self, product_id: str, qty: Any, catalogue) -> int:
        """
        Adds a product to the cart with strict validation.
        
        Steps:
            1. Validates quantity is positive integer.
            2. Checks product existence in catalogue.
            3. Checks product sellable status (e.g., expiry check).
            4. Checks current stock vs (existing cart quantity + new quantity).
        
        Args:
            product_id: ID of the product.
            qty: Quantity to add.
            catalogue: The product catalogue service.
            
        Returns:
            int: Updated quantity in cart for this product.
        """
        # Step 1: Validate quantity
        valid_qty = self._validate_quantity(qty)

        # Step 2: Validate product existence
        product = catalogue.get(product_id)  # Raises InvalidProductError if not found

        # Step 3: Check if sellable (e.g. not expired)
        if not product.is_sellable():
            raise ShoppingError(
                f"Cannot add '{product.name}': Item is expired or out of stock."
            )

        # Step 4: Check inventory limits including what is already in cart
        current_in_cart = self.items.get(product.product_id, 0)
        total_requested = current_in_cart + valid_qty

        if total_requested > product.stock:
            raise InsufficientStockError(
                f"Insufficient stock for '{product.name}'. "
                f"Requested: {valid_qty}, Already in cart: {current_in_cart}, Available stock: {product.stock}."
            )

        # Update cart dictionary
        self.items[product.product_id] = total_requested
        return total_requested

    def remove(self, product_id: str, qty: Optional[Any] = None) -> None:
        """
        Removes or decreases the quantity of a product in the cart.
        
        Args:
            product_id: ID of the product.
            qty: Quantity to remove. If None or >= current quantity, item is removed entirely.
        """
        pid = str(product_id).strip()
        if pid not in self.items:
            raise InvalidProductError(f"Product '{pid}' is not present in your shopping cart.")

        if qty is None:
            # Remove item entirely
            del self.items[pid]
            return

        valid_qty = self._validate_quantity(qty)
        current_qty = self.items[pid]

        if valid_qty >= current_qty:
            del self.items[pid]
        else:
            self.items[pid] = current_qty - valid_qty

    def lines(self, catalogue) -> List[Tuple[Any, int, float]]:
        """
        CO3: Returns cart line items as a list of tuples:
        [(product_object, quantity, line_subtotal), ...]
        """
        line_items = []
        for pid, qty in self.items.items():
            product = catalogue.get(pid)
            line_subtotal = round(product.price * qty, 2)
            # Tuple: immutable record of (Product, quantity, line_total)
            line_items.append((product, qty, line_subtotal))
        return line_items

    def get_subtotal(self, catalogue) -> float:
        """Calculates total price of all items in cart before discounts."""
        total = sum(product.price * qty for product, qty, _ in self.lines(catalogue))
        return round(total, 2)

    def is_empty(self) -> bool:
        """Returns True if the cart has no items."""
        return len(self.items) == 0

    def clear(self) -> None:
        """Empties the shopping cart."""
        self.items.clear()

    def to_dict(self, catalogue) -> Dict[str, Any]:
        """
        Formats cart state into a dictionary for JSON API responses.
        """
        items_list = []
        for product, qty, line_total in self.lines(catalogue):
            items_list.append({
                "product_id": product.product_id,
                "name": product.name,
                "category": product.category,
                "unit_price": round(product.price, 2),
                "quantity": qty,
                "line_total": line_total,
                "discount_rate": product.discount_rate(),
                "stock": product.stock
            })

        return {
            "items": items_list,
            "total_items": sum(self.items.values()),
            "subtotal": self.get_subtotal(catalogue)
        }
