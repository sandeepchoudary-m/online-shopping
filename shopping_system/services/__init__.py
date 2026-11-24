# Owner: Member 3, Catalogue and search services
"""
services/__init__.py
====================
Exposes services for catalogue management and file storage.
"""

from services.catalogue import Catalogue
from services.storage import (
    load_products,
    save_products,
    load_customers,
    save_customers,
    load_orders,
    save_orders,
    export_orders_to_csv,
    product_from_dict,
    customer_from_dict,
)

__all__ = [
    "Catalogue",
    "load_products",
    "save_products",
    "load_customers",
    "save_customers",
    "load_orders",
    "save_orders",
    "export_orders_to_csv",
    "product_from_dict",
    "customer_from_dict",
]
