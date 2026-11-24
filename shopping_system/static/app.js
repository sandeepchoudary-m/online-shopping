// Owner: Member 6 (UI logic & API integration) and Member 2 (Customer profile UI)
/* ==========================================================================
   app.js - Plain Vanilla JavaScript Client
   - No external libraries or frameworks (No React, Vue, jQuery).
   - Uses standard Fetch API to interact with Flask REST endpoints.
   - Handles errors gracefully and displays prominent alerts for live viva testing.
   ========================================================================== */

// Client State
let activeCustomerId = "C001";
let activeCustomer = null;
let currentCart = { items: [], total_items: 0, subtotal: 0.0 };
let currentProducts = [];

// =============================================================================
// API HELPER (Attaches active Customer ID header & intercepts HTTP 400 errors)
// =============================================================================

async function apiFetch(endpoint, options = {}) {
    // Merge headers with active customer ID
    const headers = {
        "Content-Type": "application/json",
        "X-Customer-ID": activeCustomerId,
        ...(options.headers || {})
    };

    try {
        const response = await fetch(endpoint, { ...options, headers });
        const data = await response.json();

        if (!response.ok) {
            // Backend returned 400 or other HTTP error
            const errorMsg = data.error || `Request failed with status ${response.status}`;
            showError(errorMsg);
            throw new Error(errorMsg);
        }

        return data;
    } catch (err) {
        // Network or JSON parsing failure
        if (!err.message.includes("Request failed")) {
            showError(err.message);
        }
        throw err;
    }
}

// =============================================================================
// ALERTS (Red for errors, green for success - vital for viva testing)
// =============================================================================

function showError(msg) {
    const box = document.getElementById("errorAlert");
    const text = document.getElementById("errorMessage");
    text.textContent = msg;
    box.style.display = "flex";

    // Auto-scroll to top so examiners see the alert immediately
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function showSuccess(msg) {
    const box = document.getElementById("successAlert");
    const text = document.getElementById("successMessage");
    text.textContent = msg;
    box.style.display = "flex";

    setTimeout(() => {
        box.style.display = "none";
    }, 4500);
}

function dismissAlert(alertId) {
    document.getElementById(alertId).style.display = "none";
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener("DOMContentLoaded", async () => {
    await loadCustomers();
    await loadCategories();
    await loadProducts();
    await loadCart();
});

// =============================================================================
// CUSTOMER PROFILE & AUTHENTICATION (Member 2)
// =============================================================================

async function loadCustomers() {
    try {
        const customers = await apiFetch("/api/customers/list");
        if (customers.length > 0) {
            // Find current active or default to first
            activeCustomer = customers.find(c => c.customer_id === activeCustomerId) || customers[0];
            activeCustomerId = activeCustomer.customer_id;
            updateCustomerNavbar(activeCustomer);
            renderCustomerPicker(customers);
        }
    } catch (e) {
        console.error("Failed to load customers:", e);
    }
}

function updateCustomerNavbar(customer) {
    document.getElementById("currentCustomerName").textContent = customer.name;
    document.getElementById("currentCustomerType").textContent = `${customer.type} Member`;
    document.getElementById("currentCustomerDiscount").textContent = `${customer.discount_percent}% Off`;
}

function renderCustomerPicker(customers) {
    const list = document.getElementById("customerPickerList");
    list.innerHTML = "";

    customers.forEach(c => {
        const item = document.createElement("div");
        item.className = `customer-option ${c.customer_id === activeCustomerId ? "active" : ""}`;
        item.innerHTML = `
            <div>
                <strong>${c.name}</strong> (${c.customer_id})
                <div style="font-size: 0.78rem; color: #64748b;">${c.email}</div>
            </div>
            <div>
                <span class="badge badge-member">${c.type}</span>
                <span class="badge badge-discount">${c.discount_percent}% Off</span>
            </div>
        `;
        item.onclick = () => switchActiveCustomer(c.customer_id);
        list.appendChild(item);
    });
}

async function switchActiveCustomer(customerId) {
    try {
        const res = await apiFetch("/api/login", {
            method: "POST",
            body: JSON.stringify({ customer_id: customerId })
        });
        activeCustomer = res.customer;
        activeCustomerId = activeCustomer.customer_id;
        updateCustomerNavbar(activeCustomer);
        closeCustomerModal();
        showSuccess(res.message);

        // Reload customer-specific cart and orders
        await loadCart();
        await loadOrders();
        await loadCustomers();
    } catch (e) {
        console.error("Login failed:", e);
    }
}

async function handleCustomerRegister(event) {
    event.preventDefault();
    const name = document.getElementById("newCustName").value.trim();
    const email = document.getElementById("newCustEmail").value.trim();
    const type = document.getElementById("newCustType").value;

    try {
        const res = await apiFetch("/api/customers", {
            method: "POST",
            body: JSON.stringify({ name, email, type })
        });
        showSuccess(res.message);
        document.getElementById("registerCustomerForm").reset();

        // Automatically switch to the newly registered customer
        await switchActiveCustomer(res.customer.customer_id);
    } catch (e) {
        console.error("Registration failed:", e);
    }
}

function openCustomerModal() {
    document.getElementById("customerModal").style.display = "flex";
}

function closeCustomerModal() {
    document.getElementById("customerModal").style.display = "none";
}

// =============================================================================
// CATALOGUE & SEARCH (Member 3)
// =============================================================================

async function loadCategories() {
    try {
        const categories = await apiFetch("/api/categories");
        const select = document.getElementById("categoryFilter");
        select.innerHTML = "";

        categories.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat;
            opt.textContent = cat === "All" ? "All Categories" : cat;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error("Failed to load categories:", e);
    }
}

async function loadProducts(searchTerm = "", category = "") {
    try {
        let url = "/api/products?";
        if (searchTerm) url += `q=${encodeURIComponent(searchTerm)}&`;
        if (category && category !== "All") url += `category=${encodeURIComponent(category)}`;

        const products = await apiFetch(url);
        currentProducts = products;
        renderProducts(products);
        populateAdminProductSelect(products);
    } catch (e) {
        console.error("Failed to load products:", e);
    }
}

function renderProducts(products) {
    const grid = document.getElementById("productsGrid");
    const countLabel = document.getElementById("resultsCount");
    grid.innerHTML = "";

    countLabel.textContent = `Showing ${products.length} product(s)`;

    if (products.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #64748b;">
                <h3>No matching products found</h3>
                <p>Try searching with another keyword or resetting category filters.</p>
            </div>
        `;
        return;
    }

    products.forEach(p => {
        const card = document.createElement("div");
        card.className = "product-card";

        // Subclass-specific badge and extra info
        let typeBadgeClass = "badge-type";
        let extraInfoHtml = "";
        let discountBadge = "";

        // Polymorphic discount display
        if (p.discount_rate > 0) {
            const pct = Math.round(p.discount_rate * 100);
            discountBadge = `<span class="product-discount-tag">${pct}% OFF</span>`;
        }

        // Subclass details
        if (p.type === "Electronics") {
            typeBadgeClass = "badge-member";
            extraInfoHtml = `<div class="product-extra-field">&#128295; Warranty: ${p.warranty_months || 12} Months</div>`;
        } else if (p.type === "Clothing") {
            typeBadgeClass = "badge-discount";
            extraInfoHtml = `<div class="product-extra-field">&#128084; Size: ${p.size || 'M'}</div>`;
        } else if (p.type === "Grocery") {
            typeBadgeClass = "badge-warning";
            const isExp = p.details && p.details.is_expired;
            const daysLeft = p.details ? p.details.days_left : 30;

            if (isExp) {
                extraInfoHtml = `<div class="product-extra-field" style="border-left-color: #ef4444; color: #dc2626;">
                    &#9888; EXPIRED on ${p.expiry_date} (Unsellable)
                </div>`;
            } else if (daysLeft <= 7) {
                extraInfoHtml = `<div class="product-extra-field" style="border-left-color: #f59e0b; color: #b45309;">
                    &#9200; Expiring in ${daysLeft} days! (Clearance 30% Off)
                </div>`;
            } else {
                extraInfoHtml = `<div class="product-extra-field">&#128197; Expiry: ${p.expiry_date}</div>`;
            }
        }

        // Stock status
        let stockHtml = "";
        if (!p.is_sellable || p.stock <= 0) {
            stockHtml = `<span class="badge badge-danger">Out of Stock</span>`;
        } else if (p.stock <= 5) {
            stockHtml = `<span class="badge badge-warning">Low Stock: ${p.stock}</span>`;
        } else {
            stockHtml = `<span class="badge badge-success">In Stock: ${p.stock}</span>`;
        }

        card.innerHTML = `
            <div>
                <div class="card-top">
                    <span class="product-id-tag">${p.product_id}</span>
                    <span class="badge ${typeBadgeClass}">${p.category}</span>
                </div>
                <h3 class="product-title">${p.name}</h3>
                <div class="product-sub-info">Type: <strong>${p.type}</strong></div>
                ${extraInfoHtml}
            </div>

            <div>
                <div class="price-stock-row">
                    <div>
                        <span class="product-price">Rs. ${p.price.toFixed(2)}</span>
                        ${discountBadge}
                    </div>
                    ${stockHtml}
                </div>

                <div class="card-actions">
                    <input type="text" class="qty-input" id="qty_${p.product_id}" value="1" placeholder="Qty">
                    <button class="btn btn-primary btn-block btn-sm" onclick="handleAddToCart('${p.product_id}')"
                        ${!p.is_sellable ? "disabled style='opacity: 0.5; cursor: not-allowed;'" : ""}>
                        &#10010; Add to Cart
                    </button>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });
}

function handleSearch() {
    const term = document.getElementById("searchInput").value;
    const cat = document.getElementById("categoryFilter").value;
    loadProducts(term, cat);
}

function resetFilters() {
    document.getElementById("searchInput").value = "";
    document.getElementById("categoryFilter").value = "All";
    loadProducts();
}

// =============================================================================
// SHOPPING CART (Member 4)
// =============================================================================

async function loadCart() {
    try {
        const cart = await apiFetch("/api/cart");
        currentCart = cart;
        renderCart(cart);
    } catch (e) {
        console.error("Failed to load cart:", e);
    }
}

function renderCart(cart) {
    const container = document.getElementById("cartItemsContainer");
    const subtotalEl = document.getElementById("cartSubtotal");
    const countBadge = document.getElementById("cartCountBadge");
    const btnCheckout = document.getElementById("btnCheckout");

    countBadge.textContent = cart.total_items || 0;
    subtotalEl.textContent = `Rs. ${(cart.subtotal || 0).toFixed(2)}`;

    container.innerHTML = "";

    if (!cart.items || cart.items.length === 0) {
        container.innerHTML = `<div class="empty-cart-msg">Your shopping cart is empty.<br>Add products from catalogue!</div>`;
        btnCheckout.disabled = true;
        btnCheckout.style.opacity = "0.5";
        return;
    }

    btnCheckout.disabled = false;
    btnCheckout.style.opacity = "1";

    cart.items.forEach(item => {
        const row = document.createElement("div");
        row.className = "cart-item-row";
        row.innerHTML = `
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <div class="cart-item-meta">Rs. ${item.unit_price.toFixed(2)} &times; ${item.quantity} = <strong>Rs. ${item.line_total.toFixed(2)}</strong></div>
            </div>
            <div class="cart-item-controls">
                <button class="btn-qty-mini" onclick="handleUpdateCartQty('${item.product_id}', 1)">+</button>
                <button class="btn-qty-mini" onclick="handleUpdateCartQty('${item.product_id}', -1)">-</button>
                <button class="btn btn-text btn-sm" onclick="handleRemoveFromCart('${item.product_id}')" title="Remove">&times;</button>
            </div>
        `;
        container.appendChild(row);
    });
}

async function handleAddToCart(productId) {
    const qtyInput = document.getElementById(`qty_${productId}`);
    const qtyVal = qtyInput ? qtyInput.value : 1;

    try {
        const res = await apiFetch("/api/cart/add", {
            method: "POST",
            body: JSON.stringify({ product_id: productId, qty: qtyVal })
        });
        showSuccess(res.message);
        await loadCart();
        // Reset qty input back to 1
        if (qtyInput) qtyInput.value = "1";
    } catch (e) {
        console.error("Add to cart error:", e);
    }
}

async function handleUpdateCartQty(productId, delta) {
    if (delta > 0) {
        try {
            await apiFetch("/api/cart/add", {
                method: "POST",
                body: JSON.stringify({ product_id: productId, qty: 1 })
            });
            await loadCart();
        } catch (e) {
            console.error("Cart increase error:", e);
        }
    } else {
        try {
            await apiFetch("/api/cart/remove", {
                method: "POST",
                body: JSON.stringify({ product_id: productId, qty: 1 })
            });
            await loadCart();
        } catch (e) {
            console.error("Cart decrease error:", e);
        }
    }
}

async function handleRemoveFromCart(productId) {
    try {
        await apiFetch("/api/cart/remove", {
            method: "POST",
            body: JSON.stringify({ product_id: productId })
        });
        await loadCart();
    } catch (e) {
        console.error("Remove from cart error:", e);
    }
}

async function clearCart() {
    try {
        await apiFetch("/api/cart/clear", { method: "POST" });
        await loadCart();
        showSuccess("Cart cleared.");
    } catch (e) {
        console.error("Clear cart error:", e);
    }
}

// =============================================================================
// CHECKOUT & INVOICE (Member 5)
// =============================================================================

async function proceedToCheckout() {
    try {
        const res = await apiFetch("/api/checkout", { method: "POST" });
        showSuccess(res.message);

        // Reload products (since stock was decremented) and empty cart
        await loadProducts();
        await loadCart();

        // Show Invoice modal
        openInvoiceModal(res.order);
    } catch (e) {
        console.error("Checkout failed:", e);
    }
}

function openInvoiceModal(order) {
    const modal = document.getElementById("invoiceModal");
    const summaryGrid = document.getElementById("invoiceSummaryGrid");
    const preText = document.getElementById("asciiInvoiceText");

    summaryGrid.innerHTML = `
        <div class="summary-box">
            <span class="summary-box-label">Order ID</span>
            <span class="summary-box-val">${order.order_id}</span>
        </div>
        <div class="summary-box">
            <span class="summary-box-label">Customer</span>
            <span class="summary-box-val">${order.customer_name}</span>
        </div>
        <div class="summary-box">
            <span class="summary-box-label">Subtotal</span>
            <span class="summary-box-val">Rs. ${order.subtotal.toFixed(2)}</span>
        </div>
        <div class="summary-box">
            <span class="summary-box-label">Product Discounts</span>
            <span class="summary-box-val" style="color: #7c3aed;">-Rs. ${order.product_discount.toFixed(2)}</span>
        </div>
        <div class="summary-box">
            <span class="summary-box-label">Member Discount</span>
            <span class="summary-box-val" style="color: #2563eb;">-Rs. ${order.member_discount.toFixed(2)}</span>
        </div>
        <div class="summary-box">
            <span class="summary-box-label">18% GST</span>
            <span class="summary-box-val">Rs. ${order.gst_amount.toFixed(2)}</span>
        </div>
        <div class="summary-box">
            <span class="summary-box-label">Grand Total</span>
            <span class="summary-box-val" style="color: #10b981;">Rs. ${order.grand_total.toFixed(2)}</span>
        </div>
    `;

    preText.textContent = order.invoice_text;
    modal.style.display = "flex";
}

function closeInvoiceModal() {
    document.getElementById("invoiceModal").style.display = "none";
}

// =============================================================================
// ORDER HISTORY (Member 5 & 6)
// =============================================================================

async function loadOrders() {
    try {
        const orders = await apiFetch("/api/orders");
        renderOrdersTable(orders);
    } catch (e) {
        console.error("Failed to load orders:", e);
    }
}

function renderOrdersTable(orders) {
    const wrapper = document.getElementById("ordersTableWrapper");
    if (!orders || orders.length === 0) {
        wrapper.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: #64748b;">
                <h3>No Orders Found</h3>
                <p>You have not placed any orders yet as ${activeCustomer ? activeCustomer.name : 'this user'}.</p>
            </div>
        `;
        return;
    }

    let rowsHtml = "";
    orders.forEach(o => {
        const itemsSummary = o.items.map(it => `${it.name} (x${it.quantity})`).join(", ");
        rowsHtml += `
            <tr>
                <td><strong>${o.order_id}</strong></td>
                <td>${o.created_at}</td>
                <td>${itemsSummary}</td>
                <td>Rs. ${o.subtotal.toFixed(2)}</td>
                <td style="color: #7c3aed;">-Rs. ${o.product_discount.toFixed(2)}</td>
                <td style="color: #2563eb;">-Rs. ${o.member_discount.toFixed(2)}</td>
                <td>Rs. ${o.gst_amount.toFixed(2)}</td>
                <td><strong>Rs. ${o.grand_total.toFixed(2)}</strong></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick='viewPastOrderInvoice(${JSON.stringify(o)})'>
                        Receipt
                    </button>
                </td>
            </tr>
        `;
    });

    wrapper.innerHTML = `
        <table class="orders-table">
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>Date & Time</th>
                    <th>Items</th>
                    <th>Subtotal</th>
                    <th>Prod. Disc</th>
                    <th>Member Disc</th>
                    <th>GST (18%)</th>
                    <th>Grand Total</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
    `;
}

function viewPastOrderInvoice(order) {
    openInvoiceModal(order);
}

// =============================================================================
// ADMIN INVENTORY MANAGEMENT
// =============================================================================

function populateAdminProductSelect(products) {
    const select = document.getElementById("adminProductSelect");
    if (!select) return;

    select.innerHTML = "";
    products.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.product_id;
        opt.textContent = `[${p.product_id}] ${p.name} (Current Stock: ${p.stock})`;
        select.appendChild(opt);
    });
}

async function handleAdminAddStock(event) {
    event.preventDefault();
    const pid = document.getElementById("adminProductSelect").value;
    const qty = parseInt(document.getElementById("adminStockQty").value, 10);

    try {
        const res = await apiFetch("/api/admin/stock", {
            method: "POST",
            body: JSON.stringify({ product_id: pid, qty })
        });
        showSuccess(res.message);
        await loadProducts();
    } catch (e) {
        console.error("Admin add stock error:", e);
    }
}

// =============================================================================
// TAB SWITCHING
// =============================================================================

function switchTab(tabName) {
    const tabs = ["catalog", "orders", "admin"];
    tabs.forEach(t => {
        const content = document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}`);
        const btn = document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}Btn`);

        if (t === tabName) {
            content.style.display = t === "catalog" ? "block" : "block";
            btn.classList.add("active");
        } else {
            content.style.display = "none";
            btn.classList.remove("active");
        }
    });

    if (tabName === "orders") {
        loadOrders();
    } else if (tabName === "catalog") {
        loadProducts();
    }
}
