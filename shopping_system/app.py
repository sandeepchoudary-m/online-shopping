# Owner: Member 2 (Customer routes & App), Member 3 (Catalogue routes), Member 4 (Cart routes), Member 5 (Checkout routes)
"""
app.py
======
Main Flask application entry point for the ShopEase Online Shopping Management System.

Architecture:
- Acts as a thin RESTful controller layer.
- Delegates business logic to models (Product, Customer, Cart, Order) and services (Catalogue, Storage).
- Keeps session state simple: in-memory dictionary `carts = {customer_id: ShoppingCart()}`.
- Global exception handler intercepts `ShoppingError` and returns `{"error": message}` with HTTP 400.
"""

import os
import io
from flask import Flask, request, jsonify, render_template, send_file, Response
from exceptions import ShoppingError, InvalidCustomerError, InvalidProductError, DataFileError
from services.catalogue import Catalogue
from services.storage import (
    load_products,
    save_products,
    ensure_default_products,
    load_customers,
    save_customers,
    ensure_default_customers,
    load_orders,
    save_orders,
    export_orders_to_csv,
    customer_from_dict
)
from models.cart import ShoppingCart
from models.order import Order

# Setup paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# In-memory application state
catalogue = Catalogue()
customers = {}
orders = []
carts = {}  # In-memory mapping: customer_id -> ShoppingCart()


def initialize_app_data():
    """
    Ensures data files exist with defaults, then loads products, customers, and orders.
    Demonstrates CO4 error handling.
    """
    global catalogue, customers, orders

    os.makedirs(DATA_DIR, exist_ok=True)
    ensure_default_products(PRODUCTS_FILE)
    ensure_default_customers(CUSTOMERS_FILE)

    try:
        catalogue = load_products(PRODUCTS_FILE)
    except DataFileError as e:
        print(f"[Warning] Failed to load products: {e}. Re-seeding defaults.")
        ensure_default_products(PRODUCTS_FILE)
        catalogue = load_products(PRODUCTS_FILE)

    try:
        customers = load_customers(CUSTOMERS_FILE)
    except DataFileError as e:
        print(f"[Warning] Failed to load customers: {e}. Re-seeding defaults.")
        ensure_default_customers(CUSTOMERS_FILE)
        customers = load_customers(CUSTOMERS_FILE)

    try:
        orders = load_orders(ORDERS_FILE)
    except DataFileError:
        orders = []


# Initialize immediately when app module is loaded
initialize_app_data()


# =============================================================================
# GLOBAL EXCEPTION HANDLER
# =============================================================================

@app.errorhandler(ShoppingError)
def handle_shopping_error(error):
    """
    Catches all domain exceptions (InvalidQuantityError, InsufficientStockError, etc.)
    and converts them to JSON responses with HTTP 400 Bad Request status code.
    """
    return jsonify({"error": str(error)}), 400


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_customer_id() -> str:
    """
    Retrieves the customer ID from request headers or parameters.
    Defaults to 'C001' (Rahul Sharma) if not explicitly provided.
    """
    # 1. Check custom header (sent by our frontend fetch calls)
    cid = request.headers.get("X-Customer-ID")
    if cid:
        return cid.strip()

    # 2. Check query string parameters
    cid = request.args.get("customer_id")
    if cid:
        return cid.strip()

    # 3. Check JSON body if available
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if "customer_id" in data:
            return str(data["customer_id"]).strip()

    # Default to first customer if available
    if customers:
        return list(customers.keys())[0]
    return "C001"


def get_current_cart(customer_id: str) -> ShoppingCart:
    """Gets or initializes the cart for a given customer."""
    if customer_id not in carts:
        carts[customer_id] = ShoppingCart()
    return carts[customer_id]


# =============================================================================
# HTML FRONTEND ROUTE
# =============================================================================

@app.route("/")
def index():
    """Renders the main single-page application."""
    return render_template("index.html")


# =============================================================================
# PRODUCTS & CATALOGUE ROUTES (Member 3)
# =============================================================================

@app.route("/api/products", methods=["GET"])
def api_products():
    """
    Lists and searches products in the catalogue.
    Query parameters:
        q: Keyword search term (matches name, category, or keywords)
        category: Category filter (e.g. 'Electronics')
    """
    term = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    matched_products = catalogue.search(term=term, category=category)
    return jsonify([p.to_dict() for p in matched_products])


@app.route("/api/categories", methods=["GET"])
def api_categories():
    """
    Returns unique product categories from the catalogue, plus 'All'.
    """
    cats = catalogue.categories()
    return jsonify(["All"] + cats)


@app.route("/api/admin/stock", methods=["POST"])
def api_admin_add_stock():
    """
    Admin route to add stock to an existing product.
    Request body: { "product_id": "P101", "qty": 10 }
    """
    data = request.get_json(force=True) or {}
    product_id = str(data.get("product_id", "")).strip()
    qty_val = data.get("qty")

    if not product_id:
        raise InvalidProductError("Product ID is required to add stock.")

    try:
        qty = int(qty_val)
        if qty <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        raise ShoppingError("Added stock quantity must be a positive integer.")

    new_stock = catalogue.add_stock(product_id, qty)
    # Persist updated stock to products.json
    save_products(catalogue, PRODUCTS_FILE)

    return jsonify({
        "message": f"Successfully added {qty} units to product '{product_id}'.",
        "product_id": product_id,
        "new_stock": new_stock
    })


# =============================================================================
# CUSTOMER ROUTES (Member 2)
# =============================================================================

@app.route("/api/customers", methods=["POST"])
def api_register_customer():
    """
    Registers a new customer.
    Request body: { "name": "...", "email": "...", "type": "Regular|Student|Premium" }
    """
    data = request.get_json(force=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    c_type = str(data.get("type", "Regular")).strip()

    if not name:
        raise InvalidCustomerError("Customer name cannot be empty.")
    if not email:
        raise InvalidCustomerError("Customer email cannot be empty.")

    # Generate sequential ID (e.g. C004)
    next_num = len(customers) + 1
    new_id = f"C{next_num:03d}"

    cust_dict = {
        "customer_id": new_id,
        "name": name,
        "email": email,
        "type": c_type
    }
    customer = customer_from_dict(cust_dict)
    customers[customer.customer_id] = customer

    # Persist to JSON
    save_customers(customers, CUSTOMERS_FILE)

    return jsonify({
        "message": "Customer registered successfully!",
        "customer": customer.to_dict()
    }), 201


@app.route("/api/customers/list", methods=["GET"])
def api_list_customers():
    """Returns all registered customers for quick switching in the UI."""
    return jsonify([c.to_dict() for c in customers.values()])


@app.route("/api/login", methods=["POST"])
def api_login():
    """
    Verifies and switches active customer by customer ID.
    Request body: { "customer_id": "C001" }
    """
    data = request.get_json(force=True) or {}
    cid = str(data.get("customer_id", "")).strip()

    if not cid or cid not in customers:
        raise InvalidCustomerError(f"Customer ID '{cid}' does not exist.")

    customer = customers[cid]
    return jsonify({
        "message": f"Logged in successfully as {customer.name} ({customer.customer_type}).",
        "customer": customer.to_dict()
    })


# =============================================================================
# SHOPPING CART ROUTES (Member 4)
# =============================================================================

@app.route("/api/cart", methods=["GET"])
def api_get_cart():
    """Returns current customer's shopping cart contents and subtotal."""
    cid = get_current_customer_id()
    cart = get_current_cart(cid)
    return jsonify(cart.to_dict(catalogue))


@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    """
    Adds an item to the cart.
    Request body: { "product_id": "P101", "qty": 2 }
    """
    cid = get_current_customer_id()
    cart = get_current_cart(cid)

    data = request.get_json(force=True) or {}
    product_id = data.get("product_id")
    qty = data.get("qty", 1)

    if not product_id:
        raise InvalidProductError("Product ID is required.")

    updated_qty = cart.add(product_id, qty, catalogue)
    return jsonify({
        "message": f"Added item to cart successfully.",
        "product_id": product_id,
        "quantity_in_cart": updated_qty,
        "cart": cart.to_dict(catalogue)
    })


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    """
    Removes or decrements an item in the cart.
    Request body: { "product_id": "P101", "qty": 1 (optional) }
    """
    cid = get_current_customer_id()
    cart = get_current_cart(cid)

    data = request.get_json(force=True) or {}
    product_id = data.get("product_id")
    qty = data.get("qty")  # None removes entire item

    if not product_id:
        raise InvalidProductError("Product ID is required.")

    cart.remove(product_id, qty)
    return jsonify({
        "message": "Item removed/updated in cart.",
        "cart": cart.to_dict(catalogue)
    })


@app.route("/api/cart/clear", methods=["POST"])
def api_cart_clear():
    """Empties the current customer's shopping cart."""
    cid = get_current_customer_id()
    cart = get_current_cart(cid)
    cart.clear()
    return jsonify({"message": "Cart cleared.", "cart": cart.to_dict(catalogue)})


# =============================================================================
# ORDER & BILLING ROUTES (Member 5)
# =============================================================================

@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    """
    Places an order:
    1. Checks stock atomically for all cart items.
    2. Deducts stock from inventory.
    3. Calculates subtotal, polymorphic product discounts, member discount, 18% GST.
    4. Generates formatted ASCII invoice.
    5. Saves order to orders.json and updates products.json.
    6. Clears customer's shopping cart.
    """
    cid = get_current_customer_id()
    if cid not in customers:
        raise InvalidCustomerError(f"Customer with ID '{cid}' was not found. Please log in.")

    customer = customers[cid]
    cart = get_current_cart(cid)

    # Generate order ID (e.g. ORD-1001)
    next_order_num = len(orders) + 1001
    order_id = f"ORD-{next_order_num}"

    # Atomic creation and stock deduction
    order = Order.create(order_id, customer, cart, catalogue)

    # Persist updated stock and new order
    orders.append(order)
    save_orders(orders, ORDERS_FILE)
    save_products(catalogue, PRODUCTS_FILE)

    # Empty the customer's cart
    cart.clear()

    return jsonify({
        "message": "Order placed successfully!",
        "order": order.to_dict()
    }), 201


@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    """
    Returns order history for the logged-in customer (or all orders if admin).
    """
    cid = get_current_customer_id()
    # Filter orders belonging to this customer
    user_orders = [o.to_dict() for o in orders if o.customer_id == cid]
    return jsonify(user_orders)


@app.route("/api/export/orders.csv", methods=["GET"])
def api_export_orders_csv():
    """
    Member 6: Downloads the complete order history as a CSV file.
    """
    csv_temp_path = os.path.join(DATA_DIR, "orders_export.csv")
    export_orders_to_csv(orders, csv_temp_path)

    with open(csv_temp_path, "r", encoding="utf-8") as f:
        csv_data = f.read()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders_export.csv"}
    )


# =============================================================================
# ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    print("=========================================================")
    print("  ShopEase Online Shopping Management System")
    print("  Server running at: http://127.0.0.1:5000")
    print("=========================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
