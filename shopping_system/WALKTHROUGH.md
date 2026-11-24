# ShopEase: Online Shopping Management System
## Code Walkthrough & Viva Guide for B.Tech CSE Students

This document is your preparation handbook for the project viva examination and live code demonstration. It explains the system architecture, breaks down each team member's contribution, maps code to syllabus Course Outcomes (CO3, CO4, CO5), provides answers to anticipated viva questions, includes a "Modify It Live" cheat sheet for examiner challenges, and outlines edge cases to demo live.

---

## 1. Quick Start Guide (3 Commands to Run and Test)

Open your terminal (PowerShell or Bash) and execute:

```bash
# Command 1: Navigate into the project directory and install Flask
cd shopping_system
pip install flask

# Command 2: Run all automated unit tests (tests validation, discounts, atomic checkout, file I/O)
python -m unittest tests/test_shopping.py

# Command 3: Start the Flask web application
python app.py
```

Now open your web browser and visit: **`http://127.0.0.1:5000`**

---

## 2. Two-Minute System Architecture & Data Flow

If the examiner asks: *"Give me a 2-minute overview of how your project works"*, explain this:

> "Our project, **ShopEase**, is an Online Shopping Management System built with a 3-tier architecture:
>
> 1. **Presentation Layer (Frontend)**: A single-page application built with clean HTML5, CSS3, and vanilla JavaScript. It uses browser `fetch()` calls to communicate asynchronously with the backend without any heavy external libraries or frameworks.
> 2. **Controller Layer (Flask API - `app.py`)**: A lightweight routing layer. It receives client HTTP requests, validates tokens/headers (`X-Customer-ID`), and delegates business logic to our specialized models and services. Any custom domain exceptions (`ShoppingError`) raised by the business logic are caught by a global error handler and returned as clean JSON responses with HTTP status `400 Bad Request`.
> 3. **Business Logic & Domain Layer (`models/` & `services/`)**:
>    - **Product Hierarchy (`models/product.py`)**: Base `Product` class with `Electronics`, `Grocery`, and `Clothing` subclasses demonstrating **polymorphism** through subclass-specific discount rates (`discount_rate()`) and expiry checks (`is_sellable()`).
>    - **Customer Hierarchy (`models/customer.py`)**: `Customer`, `StudentCustomer`, and `PremiumCustomer` demonstrating polymorphic membership discounts (0%, 5%, 10%).
>    - **Shopping Cart (`models/cart.py`)**: Enforces strict positive integer validation, inventory stock checking, and returns immutable lines as lists of tuples.
>    - **Order & Billing (`models/order.py`)**: Implements an **atomic two-phase checkout** (all items are verified before any inventory stock is deducted). Calculates subtotal, product discounts, customer member discounts, and 18% GST, then generates a formatted ASCII tax invoice.
>    - **Catalogue Service (`services/catalogue.py`)**: Manages product lookups with dictionaries, category filtering with sets, price bounds with tuples, and multi-keyword search with string operations.
> 4. **Persistence Layer (`services/storage.py`)**: Reads and writes products, customers, and orders to JSON files (`products.json`, `customers.json`, `orders.json`) and exports orders/products to CSV format. It features robust exception handling for missing files, corrupted JSON, negative prices, and duplicate IDs."

```
+-------------------------------------------------------------------------+
|                         FRONTEND (Browser UI)                           |
|       templates/index.html  |  static/style.css  |  static/app.js       |
+------------------------------------+------------------------------------+
                                     |
                       HTTP / JSON   |   fetch() with X-Customer-ID
                                     v
+-------------------------------------------------------------------------+
|                       FLASK CONTROLLER (app.py)                         |
|   Thin REST API Routes: /api/products, /api/cart, /api/checkout, etc.    |
|   Global Error Handler: Catches ShoppingError -> HTTP 400 JSON response |
+------------------+----------------------------------+-------------------+
                   |                                  |
                   v                                  v
+------------------------------------+  +---------------------------------+
|         DOMAIN MODELS              |  |            SERVICES             |
| - models/product.py  (Product OOP) |  | - services/catalogue.py         |
| - models/customer.py (Customer OOP)|  |   (dict, set, tuple, search)    |
| - models/cart.py     (Validation)  |  | - services/storage.py           |
| - models/order.py    (Atomic Bill) |  |   (JSON/CSV load/save & errors) |
| - exceptions.py      (Hierarchy)   |  +----------------+----------------+
+------------------------------------+                   |
                                                         v
                                        +---------------------------------+
                                        |          STORAGE DATA           |
                                        | - data/products.json & .csv     |
                                        | - data/customers.json           |
                                        | - data/orders.json              |
                                        +---------------------------------+
```

---

## 3. Per-Member Ownership Breakdown

### Member 1: Product Hierarchy & Custom Exceptions
- **Files Owned**: `models/product.py`, `exceptions.py`
- **Marking Criterion**: **CO5 (Object-Oriented Programming)** & **CO4 (Exceptions)**
- **What Your Code Does**:
  - Implements the custom exception hierarchy inheriting from `ShoppingError(Exception)` (`InvalidProductError`, `InsufficientStockError`, `InvalidQuantityError`, `EmptyCartError`, `InvalidCustomerError`, `DataFileError`).
  - Defines the base `Product` class with constructor `__init__(product_id, name, category, price, stock, keywords)`.
  - Implements three specialized subclasses using inheritance:
    1. `Electronics`: Adds `warranty_months`, overrides `discount_rate()` to return `0.05` (5% discount).
    2. `Grocery`: Adds `expiry_date`. If expired (`days_until_expiry() < 0`), `is_sellable()` returns `False`. If expiring within 7 days, `discount_rate()` returns `0.30` (30% clearance discount).
    3. `Clothing`: Adds `size`, overrides `discount_rate()` to return `0.15` (15% seasonal discount).
- **Key Functions to Explain**:
  - `Product.discount_rate()`: Default returns `0.0`. Subclasses override this method to provide polymorphism without `if-elif` type checks.
  - `Grocery.is_sellable()`: Checks `not self.is_expired() and self.stock > 0`. Prevents sale of expired goods.
  - `Grocery.discount_rate()`: Dynamically compares `expiry_date` with `date.today()`.
- **Top 3 Viva Questions & Answers**:
  1. *Q: What is polymorphism and where is it visible in your product classes?*  
     **A:** Polymorphism means "many forms" — calling the same method name on different objects produces class-specific behavior. In `order.py`, we call `product.discount_rate()` on every item. If the item is `Electronics`, it returns 5%; if `Clothing`, 15%; if near-expiry `Grocery`, 30%. The billing loop does not need `if isinstance()` checks.
  2. *Q: Why create custom exceptions instead of using generic Python `Exception`?*  
     **A:** Custom exceptions (`InvalidProductError`, `InsufficientStockError`) let us capture specific domain failures. Flask's `@app.errorhandler(ShoppingError)` catches all our custom errors under their common base class, letting unexpected system bugs (e.g., `ZeroDivisionError`) propagate properly during debugging.
  3. *Q: How does constructor chaining work in your subclasses?*  
     **A:** In `Electronics.__init__`, we call `super().__init__(product_id, name, category, price, stock, keywords)`. This reuses the parent `Product` initialization code and prevents code duplication (DRY principle).

---

### Member 2: Customer Hierarchy & Registration/Login Logic
- **Files Owned**: `models/customer.py`, customer routes in `app.py`, customer UI in `static/app.js`
- **Marking Criterion**: **CO5 (OOP)** & **CO3 (Data Structures)**
- **What Your Code Does**:
  - Implements the customer class hierarchy: base `Customer` (Regular member, 0% discount), `StudentCustomer` (5% member discount), and `PremiumCustomer` (10% VIP discount).
  - Handles customer registration (`POST /api/customers`) and login/switching (`POST /api/login`).
  - Stores customers in an in-memory dictionary `customers = {customer_id: Customer}` and persists them to `data/customers.json`.
- **Key Functions to Explain**:
  - `Customer.discount_rate()`: Base class returns `0.0`. `StudentCustomer` returns `0.05` and `PremiumCustomer` returns `0.10`.
  - `api_register_customer()` in `app.py`: Validates non-empty name and email, generates sequential ID (e.g., `C004`), creates the polymorphic customer object, and saves to file.
  - `api_login()` in `app.py`: Validates existence of `customer_id` and switches active session context.
- **Top 3 Viva Questions & Answers**:
  1. *Q: How does customer polymorphism integrate with order calculation?*  
     **A:** When computing an order, `order.py` calls `customer.discount_rate()`. A `StudentCustomer` gets 5% off the taxable amount after product discounts, while a `PremiumCustomer` gets 10%, without hardcoding `if customer.type == "Student"`.
  2. *Q: How does the server track which customer is currently shopping?*  
     **A:** Our frontend sends the active customer's ID in the custom HTTP request header `X-Customer-ID: C001`. Flask inspects this header with `request.headers.get("X-Customer-ID")`, ensuring cart items and order histories are mapped to the correct user.
  3. *Q: What data structure did you use to store registered customers in memory and why?*  
     **A:** A Python `dict` (`{customer_id: Customer}`). Lookups during login and checkout take $O(1)$ constant time instead of $O(N)$ linear scans through a list.

---

### Member 3: Catalogue Service & Search Logic
- **Files Owned**: `services/catalogue.py`, search routes in `app.py`
- **Marking Criterion**: **CO3 (Data Structures & String Operations)**
- **What Your Code Does**:
  - Implements the `Catalogue` class holding products in a dictionary: `{product_id: Product}`.
  - Implements multi-word, case-insensitive keyword search matching across product name, category, and keyword tags.
  - Provides unique category extraction using a `set`.
  - Provides catalogue price range using an immutable `tuple`.
- **Key Functions to Explain**:
  - `Catalogue.search(term, category)`:
    - Normalizes search string with `.strip().lower()`.
    - Splits search query into individual words: `search_words = term.lower().split()`.
    - Checks that **every** word appears in the product name, category, or keyword list:
      ```python
      for word in search_words:
          if not (word in name or word in cat or any(word in kw for kw in keywords)):
              matches = False
      ```
  - `Catalogue.categories()`:
    - Uses a `set` comprehension to eliminate duplicates: `set(p.category for p in self.products.values())`.
    - Returns a sorted list: `sorted(list(unique_categories))`.
  - `Catalogue.price_range()`:
    - Returns `(min(prices), max(prices))` as an immutable `tuple`.
- **Top 3 Viva Questions & Answers**:
  1. *Q: How does your search function handle multi-word queries like "cotton casual"?*  
     **A:** We use `term.lower().split()`, which breaks the query into a list `['cotton', 'casual']`. Our loop ensures that *every* word matches either the name, category, or any keyword of the product. If any word is missing, the product is excluded.
  2. *Q: Why use a `set` inside `categories()`?*  
     **A:** Multiple products belong to the same category (e.g., three products in "Electronics"). A Python `set` automatically discards duplicate entries. Converting it to `sorted(list(...))` produces a clean, alphabetical list for the UI dropdown.
  3. *Q: Why does `price_range()` return a tuple instead of a list?*  
     **A:** A price range consists of exactly two fixed boundaries: minimum and maximum price. Tuples are immutable and communicate that these values belong together as a fixed coordinate pair that should not be appended to or resized.

---

### Member 4: Shopping Cart & Input Validation
- **Files Owned**: `models/cart.py`, cart routes in `app.py`
- **Marking Criterion**: **CO3 (Data Structures)** & **CO4 (Validation/Exceptions)**
- **What Your Code Does**:
  - Manages active items using a dictionary: `{product_id: quantity}`.
  - Enforces strict input validation on product quantities (rejects `"abc"`, `0`, negatives, floats like `1.5`, and booleans).
  - Validates inventory limits before updating the cart, accounting for units *already* in the cart.
  - Generates cart summary lines as a **list of tuples**: `[(product, qty, line_total), ...]`.
- **Key Functions to Explain**:
  - `ShoppingCart._validate_quantity(qty)`:
    - Rejects `bool` (since `isinstance(True, int)` is True in Python).
    - Rejects `float` with `isinstance(qty, float)` to block decimal quantities like `1.5`.
    - Converts valid numeric strings using `.isdigit()`.
    - Asserts `qty > 0`.
    - Raises `InvalidQuantityError` if invalid.
  - `ShoppingCart.add(product_id, qty, catalogue)`:
    - Retrieves product via `catalogue.get(product_id)` (raises `InvalidProductError` if missing).
    - Verifies `product.is_sellable()` (blocks expired food).
    - Checks `current_in_cart + qty <= product.stock`. Raises `InsufficientStockError` if exceeded.
  - `ShoppingCart.lines(catalogue)`:
    - Builds and returns a list of tuples `(product, qty, line_total)`.
- **Top 3 Viva Questions & Answers**:
  1. *Q: Why did you block floating-point quantities like 1.5?*  
     **A:** In retail shopping for discrete inventory items (laptops, t-shirts), customers cannot purchase fractional units. We explicitly check `if isinstance(qty, float): raise InvalidQuantityError(...)`.
  2. *Q: How do you prevent a customer from adding 4 items when stock is 5, and then adding 3 more?*  
     **A:** In `cart.add()`, we check cumulative demand: `current_in_cart = self.items.get(product_id, 0)` followed by `if current_in_cart + qty > product.stock: raise InsufficientStockError(...)`.
  3. *Q: What is the benefit of returning a list of tuples from `lines()`?*  
     **A:** Each line item is an immutable snapshot `(product, quantity, line_subtotal)`. Tuples prevent callers from accidentally modifying line items in place while iterating over the cart.

---

### Member 5: Orders, Billing & Formatted Invoice
- **Files Owned**: `models/order.py`, checkout routes in `app.py`
- **Marking Criterion**: **CO5 (OOP)** & **CO3 (String Formatting)**
- **What Your Code Does**:
  - Implements **atomic two-phase checkout**:
    - **Phase 1**: Checks inventory stock for **all** items in cart. If any single item fails, it immediately raises an exception.
    - **Phase 2**: Deducts inventory stock from products.
    - **Result**: A failed checkout never leaves inventory partially decremented!
  - Executes the strict billing calculation sequence:
    1. Subtotal (sum of unit prices $\times$ quantity)
    2. Product-level polymorphic discounts
    3. Customer member discount on net amount
    4. 18% Goods & Services Tax (GST)
    5. Grand Total rounded to 2 decimal places
  - Formats an ASCII text tax invoice receipt with borders and column alignment using Python f-strings.
- **Key Functions to Explain**:
  - `Order.create(order_id, customer, cart, catalogue)`:
    - Validates cart is non-empty (`EmptyCartError`).
    - Performs atomic check-then-deduct phases.
    - Calls `product.discount_rate()` and `customer.discount_rate()`.
    - Applies `0.18` GST.
  - `Order.invoice()`:
    - Uses f-string alignment (`{self.subtotal:>12.2f}`, `{itm['name']:<22}`) and fixed-width borders (`"=" * 66`) to produce a clean receipt.
- **Top 3 Viva Questions & Answers**:
  1. *Q: Why is your checkout process called "atomic"?*  
     **A:** If a customer has 3 items in their cart, and items 1 and 2 are in stock but item 3 is out of stock, Phase 1 detects the failure on item 3 before Phase 2 begins. Because no stock was deducted for items 1 or 2, the inventory remains intact and consistent.
  2. *Q: Walk me through the exact billing calculation sequence.*  
     **A:**
     1. Calculate gross subtotal: $\sum(\text{price} \times \text{qty})$.
     2. Subtract product discounts: $\sum(\text{price} \times \text{product.discount\_rate()} \times \text{qty})$.
     3. Apply customer membership discount on remaining value: $\text{net} \times \text{customer.discount\_rate()}$.
     4. Calculate 18% GST on taxable value: $\text{taxable} \times 0.18$.
     5. Grand Total = Taxable Value + GST.
  3. *Q: Can you show me a hand-calculated verification?*  
     **A:** Yes! For a Laptop at Rs. 50,000 for a Student member:
     - Subtotal = Rs. 50,000.00
     - 5% Electronics discount = -Rs. 2,500.00 (Remaining = Rs. 47,500.00)
     - 5% Student member discount = -Rs. 2,375.00 (Taxable = Rs. 45,125.00)
     - 18% GST = Rs. 8,122.50
     - Grand Total = Rs. 53,247.50. This matches our automated test in `test_shopping.py`!

---

### Member 6: File Storage (JSON/CSV), Exception Handling & Testing
- **Files Owned**: `services/storage.py`, `tests/test_shopping.py`, `static/style.css`, CSV export routes
- **Marking Criterion**: **CO4 (File & Exception Handling)**
- **What Your Code Does**:
  - Implements polymorphic persistence: dynamically chooses JSON or CSV parser based on file extension (`.json` or `.csv`).
  - Implements factory functions (`product_from_dict`, `customer_from_dict`) to reconstruct exact OOP subclass objects from raw files.
  - Implements comprehensive try-except error handling for:
    - Missing files (`FileNotFoundError` $\rightarrow$ `DataFileError`)
    - Corrupt JSON (`json.JSONDecodeError` $\rightarrow$ `DataFileError`)
    - Negative prices/stock (`DataFileError`)
    - Duplicate product IDs (`DataFileError`)
    - Unwritable file paths (`PermissionError` / `OSError` $\rightarrow$ `DataFileError`)
  - Exports orders to structured CSV (`/api/export/orders.csv`).
  - Implements the complete automated test suite (`tests/test_shopping.py`).
- **Key Functions to Explain**:
  - `load_products(path)`: Checks extension; handles JSON or CSV parsing; maintains `seen_ids = set()` to reject duplicate IDs; wraps all failures in `DataFileError`.
  - `save_products(catalogue, path)`: Flattens keyword lists into semicolon-delimited strings for CSV or dumps JSON arrays; handles unwritable paths.
  - `export_orders_to_csv(orders, path)`: Uses Python's `csv.DictWriter` to format completed transactions into a spreadsheet-compatible format.
- **Top 3 Viva Questions & Answers**:
  1. *Q: How does `storage.py` know which subclass to instantiate when reading a JSON file?*  
     **A:** We use a Factory Pattern in `product_from_dict()`. Each JSON record includes a `"type"` field (`"Electronics"`, `"Grocery"`, `"Clothing"`). An `if-elif` checks this type and instantiates the corresponding class with its extra fields (e.g. `warranty_months`, `expiry_date`, `size`).
  2. *Q: How did you test for corrupt files and negative values?*  
     **A:** In `tests/test_shopping.py`, we use Python's `tempfile.TemporaryDirectory()`. We write invalid JSON strings like `"{ invalid json ["}` or objects with `price: -100` into a temporary file, and use `with self.assertRaises(DataFileError):` to assert that our code raises the expected exception.
  3. *Q: What happens if `data/products.json` is accidentally deleted before starting the app?*  
     **A:** `ensure_default_products()` detects that the file does not exist, automatically creates the `data/` directory, and seeds it with 10 sample products across all three categories. The application never crashes on startup!

---

## 4. Marking Rubric Evidence Table

Use this table during your evaluation to point the examiner to the exact file and lines:

| Rubric Criterion | Concept & Requirement | File Name | Exact Function / Class | Line Reference / Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **CO3** | **Dictionary**: O(1) Key-Value Mapping | `services/catalogue.py` | `Catalogue.__init__`, `Catalogue.get` | Stores all products in `self.products = {product_id: Product}` |
| **CO3** | **Dictionary**: Cart Item Quantities | `models/cart.py` | `ShoppingCart.__init__`, `add` | Maps `{product_id: qty}` for fast inventory updates |
| **CO3** | **Set**: Uniqueness Extraction | `services/catalogue.py` | `Catalogue.categories()` | `set(p.category for p in self.products.values())` eliminates duplicate categories |
| **CO3** | **List**: Ordered Collections | `services/catalogue.py` | `Catalogue.categories()` | Converts set to alphabetical list: `sorted(list(unique_categories))` |
| **CO3** | **Tuple**: Immutable Structured Records | `models/cart.py` | `ShoppingCart.lines()` | Returns immutable `[(product, qty, line_total), ...]` |
| **CO3** | **Tuple**: Fixed Coordinate Bounds | `services/catalogue.py` | `Catalogue.price_range()` | Returns `(min_price, max_price)` as an immutable tuple |
| **CO3** | **Strings**: Multi-word Query Splitting | `services/catalogue.py` | `Catalogue.search()` | `term.lower().split()` splits into tokens; verifies `all(w in ...)` |
| **CO3** | **Strings**: Formatted ASCII Invoice | `models/order.py` | `Order.invoice()` | Uses f-string padding (`:<22`, `:>12.2f`) and border multiplication (`"=" * 66`) |
| **CO4** | **File Handling**: JSON Serialization | `services/storage.py` | `load_products()`, `save_products()` | `json.load()` and `json.dump()` with UTF-8 encoding |
| **CO4** | **File Handling**: CSV Read & Write | `services/storage.py` | `load_products()`, `export_orders_to_csv()` | `csv.DictReader` and `csv.DictWriter` for spreadsheet export |
| **CO4** | **Exception**: Missing Files | `services/storage.py` | `load_products()` | Catches `FileNotFoundError`, raises clean `DataFileError` |
| **CO4** | **Exception**: Corrupted JSON Syntax | `services/storage.py` | `load_products()` | Catches `json.JSONDecodeError`, raises `DataFileError` |
| **CO4** | **Exception**: Negative Values / Bad Record| `services/storage.py` | `product_from_dict()` | Checks `if price < 0` or `stock < 0`, raises `DataFileError` |
| **CO4** | **Exception**: Duplicate Product IDs | `services/storage.py` | `load_products()` | Tracks `seen_ids = set()`, raises `DataFileError` on duplicate |
| **CO4** | **Exception**: Unwritable Paths | `services/storage.py` | `save_products()` | Catches `(OSError, PermissionError)`, raises `DataFileError` |
| **CO4** | **Exception**: Domain Hierarchy | `exceptions.py` | `ShoppingError` & Subclasses | 7 distinct custom exception classes |
| **CO5** | **OOP**: Base & Subclass Hierarchy | `models/product.py` | `Product`, `Electronics`, `Grocery`, `Clothing` | Full inheritance with `super().__init__(...)` |
| **CO5** | **OOP**: Customer Hierarchy | `models/customer.py` | `Customer`, `StudentCustomer`, `PremiumCustomer` | Base and tiered membership models |
| **CO5** | **OOP**: Visible Polymorphism | `models/order.py` | `Order.create()` | Calls `p.discount_rate()` and `customer.discount_rate()` without `if-elif` type checks |

---

## 5. "Modify It Live" Cheat Sheet for Viva Challenges

Examiners love asking students: *"Can you change the code right now so that...?"*  
Here is the exact code snippet for every common viva request:

---

### Challenge 1: "Add a new product type: Books with a 10% discount"
**File to change**: `models/product.py` (add class) and `services/storage.py` (add factory check).

1. In `models/product.py`, append this new subclass:
```python
class Book(Product):
    """Subclass representing physical books with author name."""
    def __init__(self, product_id, name, category, price, stock, keywords=None, author="Unknown"):
        super().__init__(product_id, name, category, price, stock, keywords)
        self.author = author

    def discount_rate(self) -> float:
        return 0.10  # 10% student book discount!

    def get_extra_details(self):
        return {"author": self.author}
```
2. In `services/storage.py`, inside `product_from_dict()`, add one `elif`:
```python
    elif prod_type == "Book":
        author = str(data.get("author", "Unknown"))
        return Book(prod_id, name, category, price, stock, keywords, author)
```

---

### Challenge 2: "Add a Gold Customer with a 15% discount"
**File to change**: `models/customer.py` (add class) and `services/storage.py` (add factory check).

1. In `models/customer.py`, append:
```python
class GoldCustomer(Customer):
    """VIP Gold member with 15% discount."""
    def __init__(self, customer_id: str, name: str, email: str):
        super().__init__(customer_id, name, email)
        self.customer_type = "Gold"

    def discount_rate(self) -> float:
        return 0.15  # 15% Gold discount
```
2. In `services/storage.py`, inside `customer_from_dict()`, add:
```python
    elif c_type == "gold":
        return GoldCustomer(cid, name, email)
```

---

### Challenge 3: "Change the GST tax rate from 18% to 12% (or 5%)"
**File to change**: `models/order.py` inside `Order.create()`.

Locate line ~120 in `models/order.py`:
```python
# Change this line:
gst_rate = 0.18

# To:
gst_rate = 0.12  # For 12% GST
```

---

### Challenge 4: "Add a Delivery Fee of Rs. 50 if order total is less than Rs. 500"
**File to change**: `models/order.py` inside `Order.create()`.

Inside `Order.create()`, after calculating `grand_total`:
```python
delivery_fee = 50.0 if taxable_amount < 500.0 else 0.0
grand_total = round(taxable_amount + gst_amount + delivery_fee, 2)
```

---

### Challenge 5: "Add a Bulk Discount: Buy 3 or more of any item to get an extra 5% off that item"
**File to change**: `models/order.py` inside `Order.create()`.

Inside the item iteration loop in `Order.create()`:
```python
p_disc_rate = product.discount_rate()
if qty >= 3:
    p_disc_rate += 0.05  # Extra 5% bulk discount for 3+ items!
p_disc_amt = round(line_subtotal * p_disc_rate, 2)
```

---

### Challenge 6: "Add a Search Filter by Maximum Price"
**File to change**: `services/catalogue.py` in `Catalogue.search()`.

Modify the function signature and add one `if` condition:
```python
def search(self, term: str = "", category: str = "", max_price: float = None) -> List[Product]:
    # ... inside the loop ...
    if max_price is not None and product.price > max_price:
        continue
```

---

### Challenge 7: "Sort products by price (Low to High)"
**File to change**: `services/catalogue.py` in `Catalogue.search()`.

Before `return results`:
```python
results.sort(key=lambda p: p.price)  # Ascending price sort
return results
```

---

### Challenge 8: "Print a Low-Stock Report in the Console"
**File to change**: `services/catalogue.py` (add helper method).

```python
def low_stock_report(self, threshold: int = 5) -> List[Product]:
    """Returns products where available stock is below or equal to threshold."""
    return [p for p in self.products.values() if p.stock <= threshold]
```

---

## 6. Live Edge Cases to Demonstrate

Demonstrate these scenarios in your browser during the viva to show robustness:

| Scenario | Steps to Perform in UI | Expected Result | Technical Explanation |
| :--- | :--- | :--- | :--- |
| **Invalid Quantity: String** | In any product card, type `"abc"` in the Qty box and click "Add to Cart" | A **prominent red banner** appears: `"Quantity must be a valid positive integer, received: 'abc'"` | Caught by `cart._validate_quantity()`, raises `InvalidQuantityError`, Flask returns HTTP 400. |
| **Invalid Quantity: Zero or Negative** | Type `0` or `-5` in the Qty box and click "Add to Cart" | Red banner: `"Quantity must be greater than zero, got: 0"` | Validated before modifying cart state. |
| **Invalid Quantity: Decimal Float** | Type `1.5` in the Qty box and click "Add to Cart" | Red banner: `"Quantity must be a valid positive integer, received: '1.5'"` | Discrete stock cannot be sold in fractional units. |
| **Stock Exceeded** | Find a product with 8 units in stock (e.g. Dell Laptop). Type `10` in Qty and click "Add to Cart" | Red banner: `"Insufficient stock for 'Dell Inspiron Laptop'. Requested: 10, Available stock: 8."` | `cart.add()` compares total requested units against `product.stock`. |
| **Expired Product** | Find "Artisan Sourdough Loaf" (Expired). Button is disabled or if invoked | Red banner: `"Cannot add: Item is expired or out of stock."` | `Grocery.is_sellable()` detects `days_left < 0` and blocks sale. |
| **Empty Cart Checkout** | Open app, clear cart so 0 items remain. Click "Proceed to Checkout" | Red banner: `"Cannot place order: Shopping cart is empty."` | `Order.create()` verifies cart non-empty; raises `EmptyCartError`. |
| **Deleted `products.json`** | Delete `data/products.json` on disk and restart server `python app.py` | Server automatically recreates `data/products.json` with 10 default items; page loads cleanly. | `storage.ensure_default_products()` auto-seeds sample inventory. |
| **Corrupted JSON File** | Edit `data/products.json` and type `BAD JSON SYNTAX {[` | Server detects corruption, logs warning, and regenerates valid defaults gracefully without crashing. | Caught by `json.JSONDecodeError` $\rightarrow$ `DataFileError`. |
| **Export Orders to CSV** | Click "Order History" tab $\rightarrow$ "Export All Orders to CSV" button | Browser downloads `orders_export.csv` containing all order IDs, items, and tax breakdowns. | Handled by `/api/export/orders.csv` and `csv.DictWriter`. |

---

## 7. Viva Self-Check & Final Advice for the Team

1. **Be confident**: You built a modular, production-ready system with clean OOP and robust exception handling.
2. **Know your lines**: Each team member should know the 2-3 files they own and the exact function names from Section 3.
3. **Remember the numbers**:
   - GST is **18%**.
   - Electronics discount is **5%**.
   - Clothing discount is **15%**.
   - Expiring grocery discount is **30%** (if expiring within 7 days).
   - Student discount is **5%**.
   - Premium discount is **10%**.
   - Regular customer discount is **0%**.
4. **All 9 unit tests pass**: Run `python -m unittest tests/test_shopping.py` on the examiner's laptop to prove code correctness in 0.05 seconds!
