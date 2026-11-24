// Owner: Auto-adapter for GitHub Pages Static Hosting
// Intercepts /api/ calls and serves them locally using browser localStorage
(async function() {
    let productsDB = [];
    let customersDB = [];
    let ordersDB = [];

    // Helper functions
    function getStorage(key, defaultVal) {
        try {
            const data = localStorage.getItem('shopease_' + key);
            return data ? JSON.parse(data) : defaultVal;
        } catch(e) {
            return defaultVal;
        }
    }

    function setStorage(key, val) {
        try {
            localStorage.setItem('shopease_' + key, JSON.stringify(val));
        } catch(e) {}
    }

    // Load initial seeds
    async function initDB() {
        if (!localStorage.getItem('shopease_products')) {
            try {
                const pRes = await fetch('data/products.json');
                const pData = await pRes.json();
                productsDB = pData;
                setStorage('products', productsDB);
            } catch(e) {
                productsDB = [];
            }
        } else {
            productsDB = getStorage('products', []);
        }

        if (!localStorage.getItem('shopease_customers')) {
            try {
                const cRes = await fetch('data/customers.json');
                const cData = await cRes.json();
                customersDB = cData;
                setStorage('customers', customersDB);
            } catch(e) {
                customersDB = [];
            }
        } else {
            customersDB = getStorage('customers', []);
        }

        if (!localStorage.getItem('shopease_orders')) {
            try {
                const oRes = await fetch('data/orders.json');
                const oData = await oRes.json();
                ordersDB = oData;
                setStorage('orders', ordersDB);
            } catch(e) {
                ordersDB = [];
            }
        } else {
            ordersDB = getStorage('orders', []);
        }
    }

    const initPromise = initDB();

    const originalFetch = window.fetch;
    window.fetch = async function(url, options = {}) {
        await initPromise;
        const u = typeof url === 'string' ? url : (url.url || '');
        if (!u.startsWith('/api') && !u.includes('/api/')) {
            return originalFetch.apply(this, arguments);
        }

        const method = (options.method || 'GET').toUpperCase();
        const headers = options.headers || {};
        const customerId = headers['X-Customer-ID'] || 'C001';
        let body = {};
        if (options.body) {
            try { body = JSON.parse(options.body); } catch(e) {}
        }

        const cleanPath = u.replace(/^https?:\/\/[^\/]+/, '').replace(/^.*\/api\//, '/api/');
        let cartsDB = getStorage('carts', {});

        const jsonRes = (data, status = 200) => {
            return new Response(JSON.stringify(data), {
                status: status,
                headers: { 'Content-Type': 'application/json' }
            });
        };

        // 1. Customers list
        if (cleanPath === '/api/customers/list' && method === 'GET') {
            return jsonRes(customersDB);
        }

        // 2. Login
        if (cleanPath === '/api/login' && method === 'POST') {
            const found = customersDB.find(c => c.customer_id === body.customer_id);
            if (found) {
                return jsonRes({ message: 'Logged in as ' + found.name, customer: found });
            }
            return jsonRes({ error: 'Customer not found' }, 400);
        }

        // 3. Register
        if (cleanPath === '/api/customers/register' && method === 'POST') {
            const nextId = 'C' + String(customersDB.length + 1).padStart(3, '0');
            const discount_rate = body.type === 'Premium' ? 0.1 : (body.type === 'Student' ? 0.05 : 0.0);
            const newCust = {
                customer_id: nextId,
                name: body.name,
                email: body.email,
                type: body.type,
                discount_rate: discount_rate,
                discount_percent: Math.round(discount_rate * 100)
            };
            customersDB.push(newCust);
            setStorage('customers', customersDB);
            return jsonRes({ message: 'Customer registered successfully', customer: newCust });
        }

        // 4. Categories
        if (cleanPath === '/api/categories' && method === 'GET') {
            const cats = Array.from(new Set(productsDB.map(p => p.category)));
            return jsonRes(cats);
        }

        // 5. Products list
        if (cleanPath.startsWith('/api/products') && method === 'GET') {
            return jsonRes(productsDB);
        }

        // 6. Cart view
        if (cleanPath === '/api/cart' && method === 'GET') {
            const cartItems = cartsDB[customerId] || [];
            let subtotal = 0;
            let total_items = 0;
            const items = cartItems.map(item => {
                const prod = productsDB.find(p => p.product_id === item.product_id) || {};
                const line_subtotal = (prod.price || 0) * item.quantity;
                const disc_rate = prod.discount_rate || 0;
                const prod_discount = line_subtotal * disc_rate;
                const line_total = line_subtotal - prod_discount;
                subtotal += line_total;
                total_items += item.quantity;
                return {
                    product_id: item.product_id,
                    name: prod.name || item.product_id,
                    category: prod.category || '',
                    unit_price: prod.price || 0,
                    quantity: item.quantity,
                    discount_rate: disc_rate,
                    line_subtotal: line_subtotal,
                    product_discount: prod_discount,
                    line_total: line_total
                };
            });
            return jsonRes({
                customer_id: customerId,
                items: items,
                total_items: total_items,
                subtotal: subtotal
            });
        }

        // 7. Cart Add
        if (cleanPath === '/api/cart/add' && method === 'POST') {
            if (!cartsDB[customerId]) cartsDB[customerId] = [];
            const prod = productsDB.find(p => p.product_id === body.product_id);
            if (!prod) return jsonRes({ error: 'Product not found' }, 400);
            const qty = parseInt(body.quantity || 1, 10);
            if (prod.stock < qty) return jsonRes({ error: 'Insufficient stock available' }, 400);

            const existing = cartsDB[customerId].find(i => i.product_id === body.product_id);
            if (existing) {
                if (existing.quantity + qty > prod.stock) {
                    return jsonRes({ error: 'Cannot add more than available stock' }, 400);
                }
                existing.quantity += qty;
            } else {
                cartsDB[customerId].push({ product_id: body.product_id, quantity: qty });
            }
            setStorage('carts', cartsDB);
            return jsonRes({ message: 'Item added to cart' });
        }

        // 8. Cart Update
        if (cleanPath === '/api/cart/update' && method === 'POST') {
            if (!cartsDB[customerId]) cartsDB[customerId] = [];
            const prod = productsDB.find(p => p.product_id === body.product_id);
            const qty = parseInt(body.quantity, 10);
            if (qty <= 0) {
                cartsDB[customerId] = cartsDB[customerId].filter(i => i.product_id !== body.product_id);
            } else {
                if (prod && qty > prod.stock) return jsonRes({ error: 'Quantity exceeds available stock' }, 400);
                const existing = cartsDB[customerId].find(i => i.product_id === body.product_id);
                if (existing) existing.quantity = qty;
            }
            setStorage('carts', cartsDB);
            return jsonRes({ message: 'Cart updated' });
        }

        // 9. Cart Remove
        if (cleanPath === '/api/cart/remove' && method === 'POST') {
            if (cartsDB[customerId]) {
                cartsDB[customerId] = cartsDB[customerId].filter(i => i.product_id !== body.product_id);
                setStorage('carts', cartsDB);
            }
            return jsonRes({ message: 'Item removed from cart' });
        }

        // 10. Cart Clear
        if (cleanPath === '/api/cart/clear' && method === 'POST') {
            cartsDB[customerId] = [];
            setStorage('carts', cartsDB);
            return jsonRes({ message: 'Cart cleared' });
        }

        // 11. Checkout
        if (cleanPath === '/api/checkout' && method === 'POST') {
            const cartItems = cartsDB[customerId] || [];
            if (cartItems.length === 0) return jsonRes({ error: 'Cart is empty' }, 400);

            const cust = customersDB.find(c => c.customer_id === customerId) || { name: 'Customer', type: 'Regular', discount_rate: 0 };
            let subtotal = 0;
            let product_discount = 0;
            const items = [];

            for (const item of cartItems) {
                const p = productsDB.find(prod => prod.product_id === item.product_id);
                if (!p || p.stock < item.quantity) {
                    return jsonRes({ error: 'Stock unavailable for ' + (p ? p.name : item.product_id) }, 400);
                }
            }

            for (const item of cartItems) {
                const p = productsDB.find(prod => prod.product_id === item.product_id);
                p.stock -= item.quantity;
                const line_sub = p.price * item.quantity;
                const p_disc = line_sub * (p.discount_rate || 0);
                subtotal += line_sub;
                product_discount += p_disc;
                items.push({
                    product_id: p.product_id,
                    name: p.name,
                    category: p.category,
                    unit_price: p.price,
                    quantity: item.quantity,
                    line_subtotal: line_sub,
                    discount_rate: p.discount_rate,
                    product_discount: p_disc,
                    line_total: line_sub - p_disc
                });
            }

            const afterProductDisc = subtotal - product_discount;
            const member_discount = afterProductDisc * (cust.discount_rate || 0);
            const taxable_amount = afterProductDisc - member_discount;
            const gst_amount = taxable_amount * 0.18;
            const grand_total = taxable_amount + gst_amount;
            const order_id = 'ORD-' + (1000 + ordersDB.length + 1);
            const created_at = new Date().toISOString().replace('T', ' ').substring(0, 19);

            const invoice_text = `==================================================================
                   SHOPEASE RETAIL PVT. LTD.                   
                  TAX INVOICE & CASH RECEIPT                   
==================================================================
 Order ID   : ${order_id}             Date: ${created_at}
 Customer   : ${cust.name} (${customerId})
 Membership : ${cust.type} Member
------------------------------------------------------------------
 Item Name             Qty   Rate        Disc        Amount      
------------------------------------------------------------------
` + items.map(it => ` ${it.name.padEnd(21).substring(0,21)} ${String(it.quantity).padEnd(5)} Rs.${it.unit_price.toFixed(2).padEnd(10)} -Rs.${it.product_discount.toFixed(2).padEnd(9)} Rs.${it.line_total.toFixed(2)}`).join('\n') + `
------------------------------------------------------------------
 Subtotal (Gross)                 : Rs.     ${subtotal.toFixed(2)}
 Product-Level Discounts (-)      : Rs.      ${product_discount.toFixed(2)}
 Member Discount (${cust.type}) (-)    : Rs.      ${member_discount.toFixed(2)}
 Taxable Value (Net)              : Rs.     ${taxable_amount.toFixed(2)}
 Goods & Services Tax (18% GST)   : Rs.      ${gst_amount.toFixed(2)}
==================================================================
 GRAND TOTAL (INR)                : Rs.     ${grand_total.toFixed(2)}
==================================================================
        Thank you for shopping with ShopEase! Visit Again!       
==================================================================`;

            const order = {
                order_id: order_id,
                customer_id: customerId,
                customer_name: cust.name,
                customer_type: cust.type,
                created_at: created_at,
                items: items,
                subtotal: subtotal,
                product_discount: product_discount,
                member_discount: member_discount,
                taxable_amount: taxable_amount,
                gst_amount: gst_amount,
                grand_total: grand_total,
                invoice_text: invoice_text
            };

            ordersDB.unshift(order);
            cartsDB[customerId] = [];
            setStorage('products', productsDB);
            setStorage('orders', ordersDB);
            setStorage('carts', cartsDB);

            return jsonRes({
                message: 'Order placed successfully!',
                order: order,
                invoice: invoice_text
            });
        }

        // 12. Orders
        if (cleanPath === '/api/orders' && method === 'GET') {
            const customerOrders = ordersDB.filter(o => o.customer_id === customerId);
            return jsonRes(customerOrders);
        }

        return originalFetch.apply(this, arguments);
    };
})();
