# Owner: Member 6, REST API integration verification
"""
tests/test_api.py
=================
Integration tests verifying all Flask HTTP endpoints via Flask test client.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, initialize_app_data


class TestShoppingAPI(unittest.TestCase):
    def setUp(self):
        initialize_app_data()
        self.client = app.test_client()

    def test_01_index_html(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ShopEase", res.data)

    def test_02_products_and_search(self):
        # List products
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertGreaterEqual(len(products), 8)

        # Search query
        res_search = self.client.get("/api/products?q=laptop")
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.get_json()), 1)

        # Category filter
        res_cat = self.client.get("/api/products?category=Electronics")
        self.assertEqual(res_cat.status_code, 200)
        for p in res_cat.get_json():
            self.assertEqual(p["category"], "Electronics")

    def test_03_categories(self):
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        cats = res.get_json()
        self.assertIn("All", cats)
        self.assertIn("Electronics", cats)
        self.assertIn("Clothing", cats)
        self.assertIn("Grocery", cats)

    def test_04_customer_registration_and_login(self):
        # Register new customer
        res = self.client.post("/api/customers", json={
            "name": "Kajal Sharma",
            "email": "kajal@college.edu",
            "type": "Student"
        })
        self.assertEqual(res.status_code, 201)
        new_cust = res.get_json()["customer"]
        self.assertEqual(new_cust["name"], "Kajal Sharma")
        self.assertEqual(new_cust["type"], "Student")

        # Login
        res_login = self.client.post("/api/login", json={"customer_id": new_cust["customer_id"]})
        self.assertEqual(res_login.status_code, 200)
        self.assertIn("Logged in successfully", res_login.get_json()["message"])

    def test_05_cart_and_checkout_flow(self):
        headers = {"X-Customer-ID": "C001"}

        # Clear cart first
        self.client.post("/api/cart/clear", headers=headers)

        # Add valid product
        res_add = self.client.post("/api/cart/add", json={"product_id": "P101", "qty": 1}, headers=headers)
        self.assertEqual(res_add.status_code, 200)

        # Add invalid quantity -> 400 Bad Request
        res_bad_qty = self.client.post("/api/cart/add", json={"product_id": "P101", "qty": "abc"}, headers=headers)
        self.assertEqual(res_bad_qty.status_code, 400)
        self.assertIn("error", res_bad_qty.get_json())

        # View cart
        res_cart = self.client.get("/api/cart", headers=headers)
        self.assertEqual(res_cart.status_code, 200)
        self.assertEqual(res_cart.get_json()["total_items"], 1)

        # Checkout
        res_checkout = self.client.post("/api/checkout", headers=headers)
        self.assertEqual(res_checkout.status_code, 201)
        order = res_checkout.get_json()["order"]
        self.assertIn("ORD-", order["order_id"])
        self.assertIn("invoice_text", order)

        # Order history
        res_orders = self.client.get("/api/orders", headers=headers)
        self.assertEqual(res_orders.status_code, 200)
        self.assertGreaterEqual(len(res_orders.get_json()), 1)

        # Export orders CSV
        res_csv = self.client.get("/api/export/orders.csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn(b"Order_ID", res_csv.data)

    def test_06_admin_add_stock(self):
        res = self.client.post("/api/admin/stock", json={"product_id": "P101", "qty": 5})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Successfully added", res.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
