# Owner: Member 3, Catalogue and search (dict, list, set, tuple, string ops)
"""
services/catalogue.py
=====================
Demonstrates CO3 (Data Structures & Strings):
1. Dictionary: `self.products = {product_id: Product}` providing fast O(1) key lookups.
2. Set & List: `categories()` extracts unique categories using a Python `set` and returns
   a `sorted(list(...))` to guarantee alphabetical uniqueness.
3. Tuple: `price_range()` returns an immutable `(min_price, max_price)` tuple.
4. String Operations:
   - `strip()`: Removes extraneous whitespace.
   - `lower()`: Case-insensitive searching and matching.
   - `split()`: Splits search query into multiple search tokens/words.
   - `in` operator: Checks whether each search token is a substring of product name, category, or keywords.
"""

from typing import Dict, List, Set, Tuple, Optional
from models.product import Product
from exceptions import InvalidProductError


class Catalogue:
    """
    Manages the store's in-memory product inventory, search queries, and category filtering.
    """

    def __init__(self):
        # Dictionary mapping product_id (str) -> Product object
        self.products: Dict[str, Product] = {}

    def add(self, product: Product) -> None:
        """
        Registers a product into the catalogue dictionary.
        """
        self.products[product.product_id] = product

    def get(self, product_id: str) -> Product:
        """
        Retrieves a product by its ID.
        Raises:
            InvalidProductError: If the ID does not exist in the catalogue dictionary.
        """
        pid = str(product_id).strip()
        if pid not in self.products:
            raise InvalidProductError(f"Product ID '{pid}' not found in catalogue.")
        return self.products[pid]

    def all_products(self) -> List[Product]:
        """Returns a list of all products currently in the catalogue."""
        return list(self.products.values())

    def search(self, term: str = "", category: str = "") -> List[Product]:
        """
        CO3: Search products matching keyword terms and/or category.
        
        Search Logic:
            - Splits `term` into individual words using `term.lower().split()`.
            - Requires EVERY word in the query to match at least one of:
              a) Product name
              b) Product category
              c) Any of the product keywords
            - If `category` is specified (and not 'all' or empty), filters strictly by category.
            
        Returns:
            List[Product]: Filtered list of matching products.
        """
        results: List[Product] = []

        # Sanitize category filter
        cat_clean = category.strip().lower() if category else ""

        # Sanitize and split search terms into a list of words
        search_words = term.strip().lower().split() if term else []

        for product in self.products.values():
            # 1. Check category filter
            if cat_clean and cat_clean != "all":
                if product.category.lower() != cat_clean:
                    continue

            # 2. Check keyword query (every word must match somewhere)
            if search_words:
                prod_name_lower = product.name.lower()
                prod_cat_lower = product.category.lower()
                prod_keywords_lower = [k.lower() for k in product.keywords]

                # Verify that ALL search words match this product
                matches_all_words = True
                for word in search_words:
                    word_in_name = word in prod_name_lower
                    word_in_cat = word in prod_cat_lower
                    word_in_keywords = any(word in kw for kw in prod_keywords_lower)

                    if not (word_in_name or word_in_cat or word_in_keywords):
                        matches_all_words = False
                        break

                if not matches_all_words:
                    continue

            results.append(product)

        return results

    def categories(self) -> List[str]:
        """
        CO3: Uses a `set` to extract unique category names,
        then returns a sorted `list`.
        """
        unique_categories: Set[str] = set()
        for p in self.products.values():
            if p.category:
                unique_categories.add(p.category)
        return sorted(list(unique_categories))

    def price_range(self) -> Tuple[float, float]:
        """
        CO3: Returns an immutable tuple `(min_price, max_price)` across all products.
        If catalogue is empty, returns (0.0, 0.0).
        """
        if not self.products:
            return (0.0, 0.0)

        prices = [p.price for p in self.products.values()]
        return (round(min(prices), 2), round(max(prices), 2))

    def add_stock(self, product_id: str, qty: int) -> int:
        """
        Admin helper to replenish inventory for an existing product.
        """
        product = self.get(product_id)
        if qty <= 0:
            raise ValueError("Added stock quantity must be positive.")
        product.stock += qty
        return product.stock
