# Owner: Member 5, Orders, discount and billing logic, invoice formatting
"""
models/order.py
===============
Demonstrates:
1. Two-Phase Stock Check & Deduction (Atomic Checkout):
   Verifies inventory for ALL cart items first. Only if all items pass does it deduct stock.
   This guarantees that a checkout error never leaves inventory partially decremented!
2. Polymorphic Billing Calculation:
   - Evaluates product-level discounts via `product.discount_rate()`
   - Evaluates customer-level loyalty discounts via `customer.discount_rate()`
3. Strict Billing Sequence:
   Subtotal -> Product Discounts -> Member Discount -> 18% GST -> Grand Total
4. Formatted Text Invoice generation with clean borders and alignment (CO3 string formatting).

Hand-Calculated Verification Example:
-------------------------------------
Item: Laptop (Electronics) @ Rs. 50,000.00, Quantity = 1
Customer: Student Member (5% member discount)

1. Subtotal                = 50,000.00 * 1                     = Rs. 50,000.00
2. Product Discount (5%)   = 50,000.00 * 0.05                  = Rs.  2,500.00
3. After Product Discount  = 50,000.00 - 2,500.00              = Rs. 47,500.00
4. Member Discount (5%)    = 47,500.00 * 0.05                  = Rs.  2,375.00
5. Taxable Amount          = 47,500.00 - 2,375.00              = Rs. 45,125.00
6. GST (18%)               = 45,125.00 * 0.18                  = Rs.  8,122.50
7. Grand Total             = 45,125.00 + 8,122.50              = Rs. 53,247.50
"""

from datetime import datetime
from typing import Dict, List, Any
from exceptions import EmptyCartError, InsufficientStockError


class Order:
    """
    Represents a finalized customer order and associated billing calculations.
    """

    def __init__(self, order_id: str, customer_id: str, customer_name: str,
                 customer_type: str, items: List[Dict[str, Any]], subtotal: float,
                 product_discount: float, member_discount: float, taxable_amount: float,
                 gst_amount: float, grand_total: float, created_at: str = None):
        self.order_id = order_id
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.customer_type = customer_type
        self.items = items
        self.subtotal = round(subtotal, 2)
        self.product_discount = round(product_discount, 2)
        self.member_discount = round(member_discount, 2)
        self.taxable_amount = round(taxable_amount, 2)
        self.gst_amount = round(gst_amount, 2)
        self.grand_total = round(grand_total, 2)
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def create(cls, order_id: str, customer, cart, catalogue) -> "Order":
        """
        Factory method to validate cart items, execute atomic stock deduction,
        compute all tiered discounts and taxes, and build an Order instance.
        """
        # Step 0: Ensure cart is not empty
        if cart.is_empty():
            raise EmptyCartError("Cannot place order: Shopping cart is empty.")

        # =====================================================================
        # PHASE 1: ATOMIC INVENTORY CHECK (Verify ALL items before deducting!)
        # =====================================================================
        # If any item fails, we raise an exception immediately.
        # Zero stock is deducted, leaving catalogue state untouched and consistent.
        for pid, qty in cart.items.items():
            product = catalogue.get(pid)
            if not product.is_sellable():
                raise InsufficientStockError(
                    f"Product '{product.name}' (ID: {product.product_id}) is expired or out of stock."
                )
            if qty > product.stock:
                raise InsufficientStockError(
                    f"Insufficient stock for '{product.name}'. "
                    f"Requested: {qty}, Available: {product.stock}."
                )

        # =====================================================================
        # PHASE 2: STOCK DEDUCTION
        # =====================================================================
        # Now that all items are guaranteed to have adequate stock, decrement stock.
        for pid, qty in cart.items.items():
            product = catalogue.get(pid)
            product.stock -= qty

        # =====================================================================
        # PHASE 3: BILLING & DISCOUNT CALCULATIONS
        # =====================================================================
        subtotal = 0.0
        product_discount_total = 0.0
        order_items = []

        for pid, qty in cart.items.items():
            product = catalogue.get(pid)
            line_subtotal = round(product.price * qty, 2)

            # Polymorphic call: product.discount_rate() depends on product class
            p_disc_rate = product.discount_rate()
            p_disc_amt = round(line_subtotal * p_disc_rate, 2)
            line_total = round(line_subtotal - p_disc_amt, 2)

            subtotal += line_subtotal
            product_discount_total += p_disc_amt

            order_items.append({
                "product_id": product.product_id,
                "name": product.name,
                "category": product.category,
                "unit_price": round(product.price, 2),
                "quantity": qty,
                "line_subtotal": line_subtotal,
                "discount_rate": p_disc_rate,
                "product_discount": p_disc_amt,
                "line_total": line_total
            })

        subtotal = round(subtotal, 2)
        product_discount_total = round(product_discount_total, 2)
        after_prod_discount = round(subtotal - product_discount_total, 2)

        # Polymorphic call: customer.discount_rate() depends on customer tier
        member_rate = customer.discount_rate()
        member_discount_total = round(after_prod_discount * member_rate, 2)

        taxable_amount = round(after_prod_discount - member_discount_total, 2)

        # Government GST at 18%
        gst_rate = 0.18
        gst_amount = round(taxable_amount * gst_rate, 2)

        grand_total = round(taxable_amount + gst_amount, 2)

        return cls(
            order_id=order_id,
            customer_id=customer.customer_id,
            customer_name=customer.name,
            customer_type=customer.customer_type,
            items=order_items,
            subtotal=subtotal,
            product_discount=product_discount_total,
            member_discount=member_discount_total,
            taxable_amount=taxable_amount,
            gst_amount=gst_amount,
            grand_total=grand_total
        )

    def invoice(self) -> str:
        """
        Formats and returns an ASCII text receipt / tax invoice.
        Uses string operations (f-strings, alignment, borders) satisfying CO3.
        """
        width = 66
        border = "=" * width
        divider = "-" * width

        lines = [
            border,
            "                   SHOPEASE RETAIL PVT. LTD.                   ",
            "                  TAX INVOICE & CASH RECEIPT                   ",
            border,
            f" Order ID   : {self.order_id:<20} Date: {self.created_at}",
            f" Customer   : {self.customer_name} ({self.customer_id})",
            f" Membership : {self.customer_type} Member",
            divider,
            f" {'Item Name':<22}{'Qty':<6}{'Rate':<12}{'Disc':<12}{'Amount':<12}",
            divider,
        ]

        for itm in self.items:
            name_cut = itm['name'][:20]
            rate_str = f"Rs.{itm['unit_price']:.2f}"
            disc_str = f"-Rs.{itm['product_discount']:.2f}"
            amt_str = f"Rs.{itm['line_total']:.2f}"
            lines.append(
                f" {name_cut:<22}{itm['quantity']:<6}{rate_str:<12}{disc_str:<12}{amt_str:<12}"
            )

        lines.extend([
            divider,
            f" Subtotal (Gross)                 : Rs. {self.subtotal:>12.2f}",
            f" Product-Level Discounts (-)      : Rs. {self.product_discount:>12.2f}",
            f" Member Discount ({self.customer_type}) (-)    : Rs. {self.member_discount:>12.2f}",
            f" Taxable Value (Net)              : Rs. {self.taxable_amount:>12.2f}",
            f" Goods & Services Tax (18% GST)   : Rs. {self.gst_amount:>12.2f}",
            border,
            f" GRAND TOTAL (INR)                : Rs. {self.grand_total:>12.2f}",
            border,
            "        Thank you for shopping with ShopEase! Visit Again!       ",
            border,
        ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes order for JSON storage and API responses."""
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_type": self.customer_type,
            "created_at": self.created_at,
            "items": self.items,
            "subtotal": self.subtotal,
            "product_discount": self.product_discount,
            "member_discount": self.member_discount,
            "taxable_amount": self.taxable_amount,
            "gst_amount": self.gst_amount,
            "grand_total": self.grand_total,
            "invoice_text": self.invoice()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        """Reconstructs an Order instance from dictionary data."""
        return cls(
            order_id=data["order_id"],
            customer_id=data["customer_id"],
            customer_name=data["customer_name"],
            customer_type=data.get("customer_type", "Regular"),
            items=data["items"],
            subtotal=float(data["subtotal"]),
            product_discount=float(data["product_discount"]),
            member_discount=float(data["member_discount"]),
            taxable_amount=float(data["taxable_amount"]),
            gst_amount=float(data["gst_amount"]),
            grand_total=float(data["grand_total"]),
            created_at=data.get("created_at")
        )
