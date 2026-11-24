# Owner: Member 6, Unit testing, edge cases, and file handling validation
"""
tests/test_shopping.py
======================
Comprehensive unittest suite covering:
1. Shopping cart input validation (invalid types, 0, negatives, floats).
2. Stock limits and inventory checks.
3. Polymorphic discount calculations across product types and customer tiers.
4. Exact order billing calculation with manual hand-verification in comments.
5. Search operations (single-word, multi-word, category, empty results).
6. JSON and CSV round-trip file persistence.
7. Robust error handling (missing files, corrupt JSON, negative price/stock, duplicate IDs).
8. Atomic checkout failure leaving inventory stock untouched.
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import date, timedelta

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from exceptions import (
    ShoppingError,
    InvalidProductError,
    InsufficientStockError,
    InvalidQuantityError,
    EmptyCartError,
    InvalidCustomerError,
    DataFileError
)
from models.product import Product, Electronics, Grocery, Clothing
from models.customer import Customer, StudentCustomer, PremiumCustomer
from models.cart import ShoppingCart
from models.order import Order
from services.catalogue import Catalogue
from services.storage import (
    load_products,
    save_products,
    product_from_dict,
    customer_from_dict
)


class TestShoppingSystem(unittest.TestCase):
    """Test suite for ShopEase system."""

    def setUp(self):
        """Set up a fresh catalogue, sample products, and customers before each test."""
        self.catalogue = Catalogue()

        # Electronics: 5% discount, warranty
        self.laptop = Electronics(
            product_id="P101",
            name="Dell Laptop",
            category="Electronics",
            price=50000.0,
            stock=5,
            keywords=["laptop", "computer", "dell"],
            warranty_months=24
        )
        # Clothing: 15% discount, size
        self.tshirt = Clothing(
            product_id="P102",
            name="Casual Cotton T-Shirt",
            category="Clothing",
            price=1000.0,
            stock=10,
            keywords=["tshirt", "cotton", "casual", "apparel"],
            size="L"
        )
        # Grocery: Expiring in 3 days -> 30% discount
        in_3_days = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        self.milk = Grocery(
            product_id="P103",
            name="Fresh Milk",
            category="Grocery",
            price=60.0,
            stock=20,
            keywords=["milk", "dairy", "fresh"],
            expiry_date=in_3_days
        )
        # Grocery: Expiring in 30 days -> 0% discount
        in_30_days = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.rice = Grocery(
            product_id="P104",
            name="Basmati Rice",
            category="Grocery",
            price=200.0,
            stock=15,
            keywords=["rice", "grain", "food"],
            expiry_date=in_30_days
        )
        # Grocery: Expired 5 days ago -> unsellable
        five_days_ago = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        self.expired_bread = Grocery(
            product_id="P105",
            name="Old Bread",
            category="Grocery",
            price=40.0,
            stock=5,
            keywords=["bread", "bakery"],
            expiry_date=five_days_ago
        )

        self.catalogue.add(self.laptop)
        self.catalogue.add(self.tshirt)
        self.catalogue.add(self.milk)
        self.catalogue.add(self.rice)
        self.catalogue.add(self.expired_bread)

        # Customers
        self.regular_cust = Customer("C001", "Amit Patel", "amit@yahoo.com")
        self.student_cust = StudentCustomer("C002", "Rahul Sharma", "rahul@student.edu")
        self.premium_cust = PremiumCustomer("C003", "Priya Singh", "priya@gmail.com")

    # =========================================================================
    # 1. CART QUANTITY VALIDATION
    # =========================================================================
    def test_cart_quantity_validation(self):
        """Verifies that invalid quantity formats and non-positive numbers are rejected."""
        cart = ShoppingCart()

        # Reject non-numeric strings
        with self.assertRaises(InvalidQuantityError):
            cart.add("P101", "abc", self.catalogue)

        # Reject zero
        with self.assertRaises(InvalidQuantityError):
            cart.add("P101", 0, self.catalogue)

        # Reject negative numbers
        with self.assertRaises(InvalidQuantityError):
            cart.add("P101", -5, self.catalogue)

        # Reject decimal floats (e.g. 1.5)
        with self.assertRaises(InvalidQuantityError):
            cart.add("P101", 1.5, self.catalogue)

        # Reject booleans
        with self.assertRaises(InvalidQuantityError):
            cart.add("P101", True, self.catalogue)

        # Valid positive integers must succeed
        cart.add("P101", 2, self.catalogue)
        self.assertEqual(cart.items["P101"], 2)

    # =========================================================================
    # 2. STOCK LIMITS & INVENTORY CHECKS
    # =========================================================================
    def test_stock_limits(self):
        """Verifies that adding more items than available stock raises InsufficientStockError."""
        cart = ShoppingCart()

        # Laptop has stock 5. Attempting to add 6 must fail
        with self.assertRaises(InsufficientStockError):
            cart.add("P101", 6, self.catalogue)

        # Adding 3 must succeed
        cart.add("P101", 3, self.catalogue)
        self.assertEqual(cart.items["P101"], 3)

        # Adding 3 more (total 6 > 5) must fail and keep previous 3
        with self.assertRaises(InsufficientStockError):
            cart.add("P101", 3, self.catalogue)
        self.assertEqual(cart.items["P101"], 3)

    # =========================================================================
    # 3. POLYMORPHIC DISCOUNTS
    # =========================================================================
    def test_discount_polymorphism(self):
        """
        Verifies polymorphic discount rates:
        - Electronics: 5% (0.05)
        - Clothing: 15% (0.15)
        - Grocery expiring within 7 days: 30% (0.30)
        - Fresh Grocery: 0% (0.0)
        - Expired Grocery: unsellable
        - Regular Customer: 0% (0.0)
        - Student Customer: 5% (0.05)
        - Premium Customer: 10% (0.10)
        """
        self.assertEqual(self.laptop.discount_rate(), 0.05)
        self.assertEqual(self.tshirt.discount_rate(), 0.15)
        self.assertEqual(self.milk.discount_rate(), 0.30)
        self.assertEqual(self.rice.discount_rate(), 0.0)

        # Expired product must not be sellable
        self.assertFalse(self.expired_bread.is_sellable())
        cart = ShoppingCart()
        with self.assertRaises(ShoppingError):
            cart.add("P105", 1, self.catalogue)

        # Customer discounts
        self.assertEqual(self.regular_cust.discount_rate(), 0.0)
        self.assertEqual(self.student_cust.discount_rate(), 0.05)
        self.assertEqual(self.premium_cust.discount_rate(), 0.10)

    # =========================================================================
    # 4. ORDER TOTALS & BILLING CALCULATION (Hand-verified)
    # =========================================================================
    def test_order_totals_calculation(self):
        """
        Hand-verified Order Calculation Test:
        ------------------------------------
        Cart contents:
          1. Laptop (P101, Electronics):
             Unit Price: Rs. 50,000.00
             Quantity: 1
             Line Subtotal: 50,000.00 * 1 = Rs. 50,000.00
             Electronics Discount (5%): 50,000.00 * 0.05 = Rs. 2,500.00

          2. T-Shirt (P102, Clothing):
             Unit Price: Rs. 1,000.00
             Quantity: 2
             Line Subtotal: 1,000.00 * 2 = Rs. 2,000.00
             Clothing Discount (15%): 2,000.00 * 0.15 = Rs. 300.00

        Billing Steps:
          1. Subtotal (Gross):
             50,000.00 + 2,000.00 = Rs. 52,000.00

          2. Total Product Discounts:
             2,500.00 + 300.00 = Rs. 2,800.00

          3. After Product Discounts:
             52,000.00 - 2,800.00 = Rs. 49,200.00

          4. Member Discount (Student Member @ 5%):
             49,200.00 * 0.05 = Rs. 2,460.00

          5. Taxable Amount (Net Value):
             49,200.00 - 2,460.00 = Rs. 46,740.00

          6. Goods and Services Tax (18% GST):
             46,740.00 * 0.18 = Rs. 8,413.20

          7. Grand Total (Taxable + GST):
             46,740.00 + 8,413.20 = Rs. 55,153.20
        """
        cart = ShoppingCart()
        cart.add("P101", 1, self.catalogue)  # Laptop
        cart.add("P102", 2, self.catalogue)  # T-Shirt

        order = Order.create("ORD-TEST-01", self.student_cust, cart, self.catalogue)

        self.assertEqual(order.subtotal, 52000.00)
        self.assertEqual(order.product_discount, 2800.00)
        self.assertEqual(order.member_discount, 2460.00)
        self.assertEqual(order.taxable_amount, 46740.00)
        self.assertEqual(order.gst_amount, 8413.20)
        self.assertEqual(order.grand_total, 55153.20)

        # Verify formatted invoice contains essential numbers
        inv = order.invoice()
        self.assertIn("52000.00", inv)
        self.assertIn("2800.00", inv)
        self.assertIn("2460.00", inv)
        self.assertIn("55153.20", inv)

    # =========================================================================
    # 5. SEARCH OPERATIONS (CO3: String & Data Structure Operations)
    # =========================================================================
    def test_search_features(self):
        """Verifies single-word, multi-word, category, and no-match search behaviors."""
        # Single-word search
        res1 = self.catalogue.search("laptop")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].product_id, "P101")

        # Multi-word search (every word must match name, category, or keywords)
        res2 = self.catalogue.search("cotton casual")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].product_id, "P102")

        # Category filter
        res3 = self.catalogue.search(category="Electronics")
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0].product_id, "P101")

        # No match search
        res4 = self.catalogue.search("nonexistentxyz")
        self.assertEqual(len(res4), 0)

        # Categories list (uses set under the hood to ensure uniqueness)
        cats = self.catalogue.categories()
        self.assertIn("Clothing", cats)
        self.assertIn("Electronics", cats)
        self.assertIn("Grocery", cats)
        self.assertEqual(cats, sorted(cats))

        # Price range (returns a tuple of (min, max))
        p_min, p_max = self.catalogue.price_range()
        self.assertIsInstance((p_min, p_max), tuple)
        self.assertEqual(p_min, 40.0)
        self.assertEqual(p_max, 50000.0)

    # =========================================================================
    # 6. JSON AND CSV ROUND TRIP (CO4: File Handling)
    # =========================================================================
    def test_json_and_csv_round_trip(self):
        """Verifies saving and loading products to/from JSON and CSV preserves all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test_products.json")
            csv_path = os.path.join(tmpdir, "test_products.csv")

            # 1. JSON Round-Trip
            save_products(self.catalogue, json_path)
            loaded_json_cat = load_products(json_path)
            self.assertEqual(len(loaded_json_cat.all_products()), len(self.catalogue.all_products()))
            p_json = loaded_json_cat.get("P101")
            self.assertEqual(p_json.name, "Dell Laptop")
            self.assertIsInstance(p_json, Electronics)
            self.assertEqual(p_json.warranty_months, 24)

            # 2. CSV Round-Trip
            save_products(self.catalogue, csv_path)
            loaded_csv_cat = load_products(csv_path)
            self.assertEqual(len(loaded_csv_cat.all_products()), len(self.catalogue.all_products()))
            p_csv = loaded_csv_cat.get("P102")
            self.assertEqual(p_csv.name, "Casual Cotton T-Shirt")
            self.assertIsInstance(p_csv, Clothing)
            self.assertEqual(p_csv.size, "L")

    # =========================================================================
    # 7. FILE AND EXCEPTION HANDLING (CO4)
    # =========================================================================
    def test_file_error_handling(self):
        """Verifies graceful handling of missing files, corrupt JSON, negative values, and duplicate IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Missing file
            missing_path = os.path.join(tmpdir, "does_not_exist.json")
            with self.assertRaises(DataFileError):
                load_products(missing_path)

            # Corrupt JSON syntax
            corrupt_path = os.path.join(tmpdir, "corrupt.json")
            with open(corrupt_path, "w") as f:
                f.write("{ invalid json [}")
            with self.assertRaises(DataFileError):
                load_products(corrupt_path)

            # Negative price
            bad_price_path = os.path.join(tmpdir, "bad_price.json")
            with open(bad_price_path, "w") as f:
                json.dump([{
                    "type": "Product",
                    "product_id": "P999",
                    "name": "Bad Product",
                    "category": "Test",
                    "price": -100.0,
                    "stock": 5
                }], f)
            with self.assertRaises(DataFileError):
                load_products(bad_price_path)

            # Duplicate product ID
            dup_path = os.path.join(tmpdir, "duplicate.json")
            with open(dup_path, "w") as f:
                json.dump([
                    {"type": "Product", "product_id": "P001", "name": "A", "category": "C", "price": 10, "stock": 5},
                    {"type": "Product", "product_id": "P001", "name": "B", "category": "C", "price": 20, "stock": 5}
                ], f)
            with self.assertRaises(DataFileError):
                load_products(dup_path)

            # Unsupported extension
            txt_path = os.path.join(tmpdir, "unsupported.txt")
            with open(txt_path, "w") as f:
                f.write("sample")
            with self.assertRaises(DataFileError):
                load_products(txt_path)

    # =========================================================================
    # 8. EMPTY CART CHECKOUT
    # =========================================================================
    def test_empty_cart_checkout(self):
        """Verifies that placing an order with an empty cart raises EmptyCartError."""
        empty_cart = ShoppingCart()
        with self.assertRaises(EmptyCartError):
            Order.create("ORD-EMPTY", self.student_cust, empty_cart, self.catalogue)

    # =========================================================================
    # 9. FAILED CHECKOUT LEAVES STOCK UNTOUCHED (Atomic Checkout)
    # =========================================================================
    def test_failed_checkout_leaves_stock_untouched(self):
        """
        Verifies the two-phase atomic checkout:
        If one item in the cart has insufficient stock, the checkout aborts
        and NO items have their stock decremented!
        """
        cart = ShoppingCart()
        # Item 1: Laptop has stock 5 -> requested 2
        cart.add("P101", 2, self.catalogue)

        # Directly modify cart to request 50 units of T-Shirt (available stock is only 10)
        cart.items["P102"] = 50

        initial_laptop_stock = self.laptop.stock
        initial_tshirt_stock = self.tshirt.stock

        with self.assertRaises(InsufficientStockError):
            Order.create("ORD-FAIL", self.student_cust, cart, self.catalogue)

        # Verify Laptop stock was NOT decremented despite passing its own check
        self.assertEqual(self.laptop.stock, initial_laptop_stock)
        self.assertEqual(self.tshirt.stock, initial_tshirt_stock)


if __name__ == "__main__":
    unittest.main()
