# ShopEase - Online Shopping Management System

A beginner-friendly, modular, and heavily commented prototype of an **Online Shopping Management System** built with **Python 3, Flask, and Vanilla JavaScript**. Designed for B.Tech Computer Science & Engineering university course evaluations.

---

## 📌 Project Overview

**ShopEase** manages an end-to-end retail shopping experience:
1. **Product Catalogue**: Browse inventory with category filters and multi-word keyword search.
2. **Specialized Product Discounts**: Polymorphic discount rates for Electronics (5%), Clothing (15%), and near-expiry Groceries (30%). Expired products cannot be sold.
3. **Customer Tiers**: Polymorphic member loyalty discounts for Regular (0%), Student (5%), and Premium (10%) shoppers.
4. **Shopping Cart**: Real-time cart with quantity validation (rejecting negative numbers, zeros, floats, strings) and inventory limits.
5. **Atomic Checkout & Billing**: Two-phase stock deduction that guarantees zero stock updates on failure, followed by sequential billing (Subtotal $\rightarrow$ Product Discounts $\rightarrow$ Member Discount $\rightarrow$ 18% GST $\rightarrow$ Grand Total) and tax receipt generation.
6. **Robust File Storage**: JSON and CSV load/save handling missing files, corrupted JSON syntax, duplicate IDs, and unwritable paths.

---

## 🛠 Tech Stack (100% Offline Capable)

- **Backend**: Python 3.8+ & **Flask** (the only external dependency).
- **Frontend**: Plain HTML5, CSS3 (Modern Flexbox/Grid, responsive), and Vanilla JavaScript (Fetch API). **No React, Vue, jQuery, or Tailwind**. Works completely offline without CDNs.
- **Storage**: JSON files (`data/products.json`, `data/customers.json`, `data/orders.json`) and CSV export (`orders_export.csv`).
- **Testing**: Python's built-in `unittest` framework.

---

## 📂 Project Structure

```text
shopping_system/
├── app.py                  # Thin Flask routes controller (Member 2, 3, 4, 5)
├── models/
│   ├── __init__.py         # Package exports
│   ├── product.py          # Product, Electronics, Grocery, Clothing (Member 1)
│   ├── customer.py         # Customer, StudentCustomer, PremiumCustomer (Member 2)
│   ├── cart.py             # ShoppingCart with validation (Member 4)
│   └── order.py            # Order, atomic billing, ASCII invoice (Member 5)
├── services/
│   ├── __init__.py         # Package exports
│   ├── catalogue.py        # Catalogue dict, multi-word search, set, tuple (Member 3)
│   └── storage.py          # JSON/CSV file I/O and robust exceptions (Member 6)
├── exceptions.py           # Custom exception hierarchy (Member 1)
├── data/                   # Auto-created sample JSON storage files
│   ├── products.json
│   ├── customers.json
│   └── orders.json
├── static/
│   ├── style.css           # Pure responsive CSS with red error banners (Member 6)
│   └── app.js              # Vanilla JS fetch logic & customer UI (Member 6 & 2)
├── templates/
│   └── index.html          # Clean Single-Page UI (Member 6 & 2)
├── tests/
│   ├── test_shopping.py    # Comprehensive unittest test suite (Member 6)
│   └── test_api.py         # Flask REST API integration tests (Member 6)
├── WALKTHROUGH.md          # Complete viva preparation & live code modification guide
└── README.md               # Project documentation
```

---

## 🚀 Quick Start (Run in 3 Steps)

### Step 1: Install Flask
```bash
cd shopping_system
pip install flask
```

### Step 2: Run Unit Tests
```bash
python -m unittest tests/test_shopping.py
```
*(All 9 unit tests pass in under 0.1 seconds).*

### Step 3: Start the Application
```bash
python app.py
```
Open your web browser and go to:
👉 **`http://127.0.0.1:5000`**

---

## 👥 Team Split & Responsibilities (6 Members)

| Member | Focus Area | Files Owned | Rubric Focus |
| :---: | :--- | :--- | :---: |
| **Member 1** | Product OOP Hierarchy & Custom Exception Classes | `models/product.py`, `exceptions.py` | **CO5 & CO4** |
| **Member 2** | Customer Hierarchy, Registration & Login Logic | `models/customer.py`, routes in `app.py` | **CO5 & CO3** |
| **Member 3** | Catalogue Service, Set/Tuple structures & Search | `services/catalogue.py`, search routes | **CO3** |
| **Member 4** | Shopping Cart, Quantity Validation & Stock limits | `models/cart.py`, cart routes | **CO3 & CO4** |
| **Member 5** | Atomic Checkout, Billing Sequence & Text Receipt | `models/order.py`, checkout routes | **CO5 & CO3** |
| **Member 6** | File I/O (JSON/CSV), Exception Handling & Testing | `services/storage.py`, `tests/`, `static/style.css` | **CO4** |

---

## 🎯 Syllabus & Marking Rubric Mapping

### 1. CO3: Data Structures & String Operations (10/10)
- **Dictionaries**: Fast $O(1)$ lookups in product catalogue (`self.products`), customer cart mappings (`self.items`), and active user accounts (`customers`).
- **Sets**: Unique category deduplication in `Catalogue.categories()` (`set(p.category for p in ...)`).
- **Lists**: Clean sorted collections for search results and category dropdowns.
- **Tuples**: Immutable line item records `(product, qty, line_total)` in `ShoppingCart.lines()` and boundary coordinates `(min_price, max_price)` in `Catalogue.price_range()`.
- **String Operations**: `.lower()`, `.strip()`, `.split()` for multi-word search, `in` keyword checks, and formatted f-strings for receipts.

### 2. CO4: File and Exception Handling (10/10)
- **JSON & CSV Support**: Automatic detection by file extension (`.json` or `.csv`).
- **Comprehensive Try-Except**: Catches `FileNotFoundError`, `json.JSONDecodeError`, negative prices/stocks, duplicate IDs, and unwritable directories, translating them into `DataFileError`.
- **Domain Exception Hierarchy**: 7 custom exceptions derived from `ShoppingError(Exception)`.

### 3. CO5: Object-Oriented Programming (10/10)
- **Class Hierarchies**: `Product` $\rightarrow$ `Electronics`, `Grocery`, `Clothing`; `Customer` $\rightarrow$ `StudentCustomer`, `PremiumCustomer`.
- **Constructor Chaining**: Subclasses reuse parent logic with `super().__init__(...)`.
- **Polymorphism**: `product.discount_rate()`, `product.is_sellable()`, and `customer.discount_rate()` called seamlessly without any `isinstance()` branching.

---

## 🧪 Automated Test Suite

Run the unit tests anytime:
```bash
python -m unittest tests/test_shopping.py
```

Test coverage includes:
- [x] Input validation (rejects strings like `"abc"`, zero `0`, negative numbers `-1`, decimal floats `1.5`, booleans)
- [x] Inventory limits and cumulative stock enforcement
- [x] Subclass-specific polymorphic discounts (5%, 15%, 30%, 0%)
- [x] Expired product detection (unsellable)
- [x] Hand-verified order billing calculation (subtotal, product discounts, student discounts, 18% GST)
- [x] Multi-keyword search across names, categories, and tags
- [x] JSON and CSV round-trip persistence
- [x] Graceful handling of missing files and corrupted JSON
- [x] Rejection of negative prices and duplicate product IDs
- [x] Empty cart checkout prevention
- [x] Atomic two-phase checkout (verifying stock untouched on failed checkout)

---

## 📖 Viva Preparation

Read **`WALKTHROUGH.md`** for:
- Detailed per-member explanation of code and functions.
- 3 anticipated viva questions and answers per member.
- "Modify It Live" cheat sheet for instant code changes during examiner questioning.
- Step-by-step edge cases to demo live.
