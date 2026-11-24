# Owner: Member 6, File handling (JSON/CSV) and exception handling
"""
services/storage.py
===================
Demonstrates CO4 (File and Exception Handling):
1. Format Handling: Dynamically selects JSON or CSV handler based on file extension.
2. Robust Exception Handling (try-except):
   - FileNotFoundError -> raises DataFileError("File not found: ...")
   - json.JSONDecodeError -> raises DataFileError("Corrupt JSON format ...")
   - Missing fields / Invalid values (e.g. negative price) -> raises DataFileError(...)
   - Unknown subclass type -> raises DataFileError("Unknown product type ...")
   - Duplicate product IDs -> raises DataFileError("Duplicate product ID ...")
   - PermissionError / OSError (unwritable path) -> raises DataFileError(...)
3. Auto-seeding: Automatically provisions sample data files if not already present.
"""

import os
import json
import csv
from typing import Dict, List, Any
from exceptions import DataFileError
from models.product import Product, Electronics, Grocery, Clothing
from models.customer import Customer, StudentCustomer, PremiumCustomer
from models.order import Order
from services.catalogue import Catalogue


# =============================================================================
# FACTORY FUNCTIONS (Converts raw dicts to polymorphic OOP instances)
# =============================================================================

def product_from_dict(data: Dict[str, Any]) -> Product:
    """
    Factory function: Instantiates the appropriate Product subclass based on 'type'.
    Validates field presence and realistic numeric ranges (e.g. non-negative price).
    
    Raises:
        DataFileError: If required fields are missing, invalid, or type is unknown.
    """
    # 1. Validate required fields
    required = ["product_id", "name", "category", "price", "stock"]
    for field in required:
        if field not in data:
            raise DataFileError(f"Missing required product field: '{field}' in record: {data}")

    # 2. Validate price and stock values
    try:
        price = float(data["price"])
        if price < 0:
            raise DataFileError(f"Invalid price {price}: Product price cannot be negative.")
    except (ValueError, TypeError):
        raise DataFileError(f"Invalid price format '{data.get('price')}'. Must be numeric.")

    try:
        stock = int(data["stock"])
        if stock < 0:
            raise DataFileError(f"Invalid stock {stock}: Product stock cannot be negative.")
    except (ValueError, TypeError):
        raise DataFileError(f"Invalid stock format '{data.get('stock')}'. Must be an integer.")

    prod_id = str(data["product_id"]).strip()
    name = str(data["name"]).strip()
    category = str(data["category"]).strip()
    keywords = data.get("keywords", [])
    prod_type = str(data.get("type", "Product")).strip()

    # 3. Instantiate appropriate subclass based on 'type'
    if prod_type == "Electronics":
        warranty = int(data.get("warranty_months", 12))
        return Electronics(prod_id, name, category, price, stock, keywords, warranty)

    elif prod_type == "Grocery":
        expiry = str(data.get("expiry_date", "2026-12-31")).strip()
        return Grocery(prod_id, name, category, price, stock, keywords, expiry)

    elif prod_type == "Clothing":
        size = str(data.get("size", "M")).strip()
        return Clothing(prod_id, name, category, price, stock, keywords, size)

    elif prod_type == "Product":
        return Product(prod_id, name, category, price, stock, keywords)

    else:
        raise DataFileError(f"Unknown product type: '{prod_type}'. Cannot deserialize product.")


def customer_from_dict(data: Dict[str, Any]) -> Customer:
    """
    Factory function: Instantiates Customer or specialized customer subclass.
    """
    if "customer_id" not in data or "name" not in data:
        raise DataFileError(f"Invalid customer record: {data}")

    cid = str(data["customer_id"]).strip()
    name = str(data["name"]).strip()
    email = str(data.get("email", "")).strip()
    c_type = str(data.get("type", "Regular")).strip().lower()

    if c_type == "student":
        return StudentCustomer(cid, name, email)
    elif c_type == "premium":
        return PremiumCustomer(cid, name, email)
    else:
        return Customer(cid, name, email)


# =============================================================================
# PRODUCT CATALOGUE PERSISTENCE (JSON & CSV)
# =============================================================================

def load_products(path: str) -> Catalogue:
    """
    Loads products from either a JSON or CSV file into a Catalogue object.
    
    Demonstrates CO4:
        - Extension checking (.json / .csv)
        - FileNotFoundError handling
        - json.JSONDecodeError handling
        - Duplicate ID detection
    """
    if not os.path.exists(path):
        raise DataFileError(f"Products file not found at path: '{path}'")

    ext = os.path.splitext(path)[1].lower()
    catalogue = Catalogue()
    seen_ids = set()

    if ext == ".json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise DataFileError(f"Corrupt JSON syntax in file '{path}': {e}")
        except (OSError, PermissionError) as e:
            raise DataFileError(f"Failed to read file '{path}': {e}")

        if not isinstance(raw_data, list):
            raise DataFileError(f"Invalid JSON root structure in '{path}'. Expected a list of products.")

        for item in raw_data:
            prod = product_from_dict(item)
            if prod.product_id in seen_ids:
                raise DataFileError(f"Duplicate product ID found in file '{path}': '{prod.product_id}'")
            seen_ids.add(prod.product_id)
            catalogue.add(prod)

    elif ext == ".csv":
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse keywords string into list
                    kw_str = row.get("keywords", "")
                    keywords_list = [k.strip() for k in kw_str.split(";") if k.strip()]
                    row["keywords"] = keywords_list

                    prod = product_from_dict(row)
                    if prod.product_id in seen_ids:
                        raise DataFileError(f"Duplicate product ID found in file '{path}': '{prod.product_id}'")
                    seen_ids.add(prod.product_id)
                    catalogue.add(prod)
        except (OSError, PermissionError) as e:
            raise DataFileError(f"Failed to read CSV file '{path}': {e}")
    else:
        raise DataFileError(f"Unsupported file format: '{ext}'. Only .json and .csv are supported.")

    return catalogue


def save_products(catalogue: Catalogue, path: str) -> None:
    """
    Saves products from a Catalogue object into either a JSON or CSV file.
    
    Demonstrates CO4:
        - Catches PermissionError/OSError for unwritable paths
        - Exports structured data
    """
    ext = os.path.splitext(path)[1].lower()
    products_list = [p.to_dict() for p in catalogue.all_products()]

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    try:
        if ext == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(products_list, f, indent=4)

        elif ext == ".csv":
            fieldnames = [
                "type", "product_id", "name", "category", "price",
                "stock", "keywords", "warranty_months", "expiry_date", "size"
            ]
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for p in products_list:
                    # Flatten keywords into a semicolon-separated string for CSV
                    row = dict(p)
                    row["keywords"] = ";".join(p.get("keywords", []))
                    writer.writerow(row)
        else:
            raise DataFileError(f"Unsupported export file format: '{ext}'. Must be .json or .csv.")
    except (OSError, PermissionError) as e:
        raise DataFileError(f"Cannot write products to path '{path}': {e}")


# =============================================================================
# DEFAULT SEED DATA
# =============================================================================

def get_default_sample_products() -> List[Dict[str, Any]]:
    """Returns 8-10 diverse sample products across all subclasses."""
    return [
        {
            "type": "Electronics",
            "product_id": "P101",
            "name": "Dell Inspiron Laptop",
            "category": "Electronics",
            "price": 52000.00,
            "stock": 8,
            "keywords": ["laptop", "computer", "dell", "intel", "work"],
            "warranty_months": 24
        },
        {
            "type": "Electronics",
            "product_id": "P102",
            "name": "Boat Rockerz Headphones",
            "category": "Electronics",
            "price": 1499.00,
            "stock": 15,
            "keywords": ["headphones", "boat", "audio", "bluetooth", "music"],
            "warranty_months": 12
        },
        {
            "type": "Electronics",
            "product_id": "P103",
            "name": "Samsung Galaxy Smartphone",
            "category": "Electronics",
            "price": 24999.00,
            "stock": 10,
            "keywords": ["mobile", "phone", "samsung", "galaxy", "5g"],
            "warranty_months": 12
        },
        {
            "type": "Clothing",
            "product_id": "P104",
            "name": "Casual Cotton T-Shirt",
            "category": "Clothing",
            "price": 799.00,
            "stock": 20,
            "keywords": ["tshirt", "cotton", "clothing", "casual", "shirt"],
            "size": "L"
        },
        {
            "type": "Clothing",
            "product_id": "P105",
            "name": "Slim Fit Denim Jeans",
            "category": "Clothing",
            "price": 1599.00,
            "stock": 12,
            "keywords": ["jeans", "denim", "pants", "clothing", "blue"],
            "size": "32"
        },
        {
            "type": "Clothing",
            "product_id": "P106",
            "name": "Puma Running Shoes",
            "category": "Clothing",
            "price": 2899.00,
            "stock": 6,
            "keywords": ["shoes", "running", "sports", "puma", "footwear"],
            "size": "9"
        },
        {
            "type": "Grocery",
            "product_id": "P107",
            "name": "Amul Fresh Full Cream Milk",
            "category": "Grocery",
            "price": 66.00,
            "stock": 25,
            "keywords": ["milk", "dairy", "amul", "fresh", "grocery"],
            "expiry_date": "2026-11-23"  # Expiring in ~4 days (Qualifies for 30% discount!)
        },
        {
            "type": "Grocery",
            "product_id": "P108",
            "name": "Fortune Premium Basmati Rice (5kg)",
            "category": "Grocery",
            "price": 450.00,
            "stock": 18,
            "keywords": ["rice", "grain", "basmati", "fortune", "food"],
            "expiry_date": "2027-06-30"  # Fresh (> 7 days remaining)
        },
        {
            "type": "Grocery",
            "product_id": "P109",
            "name": "Epigamia Greek Yogurt",
            "category": "Grocery",
            "price": 85.00,
            "stock": 14,
            "keywords": ["yogurt", "dairy", "epigamia", "snack"],
            "expiry_date": "2026-11-24"  # Expiring in ~5 days (Qualifies for 30% discount!)
        },
        {
            "type": "Grocery",
            "product_id": "P110",
            "name": "Artisan Sourdough Loaf (Sample Expired)",
            "category": "Grocery",
            "price": 120.00,
            "stock": 3,
            "keywords": ["bread", "bakery", "sourdough"],
            "expiry_date": "2026-11-10"  # Expired! Not sellable (for live viva edge case demo)
        }
    ]


def ensure_default_products(path: str) -> None:
    """Creates sample products.json if missing."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        samples = get_default_sample_products()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(samples, f, indent=4)


# =============================================================================
# CUSTOMER PERSISTENCE
# =============================================================================

def load_customers(path: str) -> Dict[str, Customer]:
    """Loads registered customers from a JSON file."""
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise DataFileError(f"Error loading customers from '{path}': {e}")

    customers = {}
    for item in data:
        cust = customer_from_dict(item)
        customers[cust.customer_id] = cust
    return customers


def save_customers(customers: Dict[str, Customer], path: str) -> None:
    """Saves registered customers to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    customer_list = [c.to_dict() for c in customers.values()]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(customer_list, f, indent=4)
    except (OSError, PermissionError) as e:
        raise DataFileError(f"Cannot save customers to '{path}': {e}")


def ensure_default_customers(path: str) -> None:
    """Seeds sample customers if data/customers.json does not exist."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        seed_customers = [
            {"customer_id": "C001", "name": "Rahul Sharma", "email": "rahul@student.edu", "type": "Student"},
            {"customer_id": "C002", "name": "Priya Singh", "email": "priya.singh@gmail.com", "type": "Premium"},
            {"customer_id": "C003", "name": "Amit Patel", "email": "amit.patel@yahoo.com", "type": "Regular"}
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(seed_customers, f, indent=4)


# =============================================================================
# ORDER PERSISTENCE & CSV EXPORT
# =============================================================================

def load_orders(path: str) -> List[Order]:
    """Loads all completed orders from a JSON file."""
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise DataFileError(f"Error loading orders from '{path}': {e}")

    return [Order.from_dict(o) for o in data]


def save_orders(orders: List[Order], path: str) -> None:
    """Saves all completed orders to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    orders_data = [o.to_dict() for o in orders]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(orders_data, f, indent=4)
    except (OSError, PermissionError) as e:
        raise DataFileError(f"Cannot save orders to '{path}': {e}")


def export_orders_to_csv(orders: List[Order], path: str) -> None:
    """
    Exports order history into a structured CSV file for audit and Excel download.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fieldnames = [
        "Order_ID", "Customer_ID", "Customer_Name", "Customer_Type", "Date",
        "Subtotal", "Product_Discount", "Member_Discount", "Taxable_Amount",
        "GST_18%", "Grand_Total", "Items_Summary"
    ]

    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for o in orders:
                items_summary = "; ".join([f"{it['name']} x{it['quantity']}" for it in o.items])
                writer.writerow({
                    "Order_ID": o.order_id,
                    "Customer_ID": o.customer_id,
                    "Customer_Name": o.customer_name,
                    "Customer_Type": o.customer_type,
                    "Date": o.created_at,
                    "Subtotal": f"{o.subtotal:.2f}",
                    "Product_Discount": f"{o.product_discount:.2f}",
                    "Member_Discount": f"{o.member_discount:.2f}",
                    "Taxable_Amount": f"{o.taxable_amount:.2f}",
                    "GST_18%": f"{o.gst_amount:.2f}",
                    "Grand_Total": f"{o.grand_total:.2f}",
                    "Items_Summary": items_summary
                })
    except (OSError, PermissionError) as e:
        raise DataFileError(f"Cannot export orders to CSV at '{path}': {e}")
