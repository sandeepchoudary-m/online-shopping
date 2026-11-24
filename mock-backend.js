// Owner: Auto-adapter for GitHub Pages Static Hosting
// Intercepts /api/ calls and serves them locally using browser localStorage
(async function() {
    const DEFAULT_PRODUCTS = [
        {
            "type": "Electronics",
            "product_id": "P101",
            "name": "Dell Inspiron Laptop",
            "category": "Electronics",
            "price": 52000.0,
            "stock": 19,
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=300&q=80",
            "keywords": ["laptop", "computer", "dell", "intel", "work"],
            "discount_rate": 0.05,
            "is_sellable": true,
            "details": { "warranty_months": 24 },
            "warranty_months": 24
        },
        {
            "type": "Electronics",
            "product_id": "P102",
            "name": "Boat Rockerz Headphones",
            "category": "Electronics",
            "price": 1499.0,
            "stock": 15,
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&q=80",
            "keywords": ["headphones", "boat", "audio", "bluetooth", "music"],
            "discount_rate": 0.05,
            "is_sellable": true,
            "details": { "warranty_months": 12 },
            "warranty_months": 12
        },
        {
            "type": "Electronics",
            "product_id": "P103",
            "name": "Samsung Galaxy Smartphone",
            "category": "Electronics",
            "price": 24999.0,
            "stock": 10,
            "image_url": "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=300&q=80",
            "keywords": ["mobile", "phone", "samsung", "galaxy", "5g"],
            "discount_rate": 0.05,
            "is_sellable": true,
            "details": { "warranty_months": 12 },
            "warranty_months": 12
        },
        {
            "type": "Clothing",
            "product_id": "P104",
            "name": "Casual Cotton T-Shirt",
            "category": "Clothing",
            "price": 799.0,
            "stock": 20,
            "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=300&q=80",
            "keywords": ["tshirt", "cotton", "clothing", "casual", "shirt"],
            "discount_rate": 0.15,
            "is_sellable": true,
            "details": { "size": "L" },
            "size": "L"
        },
        {
            "type": "Clothing",
            "product_id": "P105",
            "name": "Slim Fit Denim Jeans",
            "category": "Clothing",
            "price": 1599.0,
            "stock": 12,
            "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=300&q=80",
            "keywords": ["jeans", "denim", "pants", "clothing", "blue"],
            "discount_rate": 0.15,
            "is_sellable": true,
            "details": { "size": "32" },
            "size": "32"
        },
        {
            "type": "Clothing",
            "product_id": "P106",
            "name": "Puma Running Shoes",
            "category": "Clothing",
            "price": 2899.0,
            "stock": 6,
            "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300&q=80",
            "keywords": ["shoes", "running", "sports", "puma", "footwear"],
            "discount_rate": 0.15,
            "is_sellable": true,
            "details": { "size": "9" },
            "size": "9"
        },
        {
            "type": "Grocery",
            "product_id": "P107",
            "name": "Amul Fresh Full Cream Milk",
            "category": "Grocery",
            "price": 66.0,
            "stock": 25,
            "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&q=80",
            "keywords": ["milk", "dairy", "amul", "fresh", "grocery"],
            "discount_rate": 0.3,
            "is_sellable": true,
            "details": { "expiry_date": "2026-11-23", "days_left": 4, "is_expired": false },
            "expiry_date": "2026-11-23",
            "days_left": 4,
            "is_expired": false
        },
        {
            "type": "Grocery",
            "product_id": "P108",
            "name": "Fortune Premium Basmati Rice (5kg)",
            "category": "Grocery",
            "price": 450.0,
            "stock": 18,
            "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&q=80",
            "keywords": ["rice", "grain", "basmati", "fortune", "food"],
            "discount_rate": 0.0,
            "is_sellable": true,
            "details": { "expiry_date": "2027-06-30", "days_left": 223, "is_expired": false },
            "expiry_date": "2027-06-30",
            "days_left": 223,
            "is_expired": false
        },
        {
            "type": "Grocery",
            "product_id": "P109",
            "name": "Epigamia Greek Yogurt",
            "category": "Grocery",
            "price": 85.0,
            "stock": 14,
            "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=300&q=80",
            "keywords": ["yogurt", "dairy", "epigamia", "snack"],
            "discount_rate": 0.3,
            "is_sellable": true,
            "details": { "expiry_date": "2026-11-24", "days_left": 5, "is_expired": false },
            "expiry_date": "2026-11-24",
            "days_left": 5,
            "is_expired": false
        },
        {
            "type": "Grocery",
            "product_id": "P110",
            "name": "Artisan Sourdough Loaf (Sample Expired)",
            "category": "Grocery",
            "price": 120.0,
            "stock": 3,
            "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&q=80",
            "keywords": ["bread", "bakery", "sourdough"],
            "discount_rate": 0.0,
            "is_sellable": false,
            "details": { "expiry_date": "2026-11-10", "days_left": -9, "is_expired": true },
            "expiry_date": "2026-11-10",
            "days_left": -9,
            "is_expired": true
        }
    ];

    const DEFAULT_CUSTOMERS = [
        {
            "customer_id": "C001",
            "name": "Rahul Sharma",
            "email": "rahul@student.edu",
            "type": "Student",
            "discount_rate": 0.05,
            "discount_percent": 5
        },
        {
            "customer_id": "C002",
            "name": "Priya Singh",
            "email": "priya.singh@gmail.com",
            "type": "Premium",
            "discount_rate": 0.1,
            "discount_percent": 10
        },
        {
            "customer_id": "C003",
            "name": "Amit Patel",
            "email": "amit.patel@yahoo.com",
            "type": "Regular",
            "discount_rate": 0.0,
            "discount_percent": 0
        }
    ];

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
        const storedProducts = getStorage('products', null);
        if (!storedProducts || storedProducts.length === 0 || !storedProducts[0].image_url) {
            productsDB = DEFAULT_PRODUCTS;
            setStorage('products', productsDB);
        } else {
            productsDB = storedProducts;
        }

        const storedCustomers = getStorage('customers', null);
        if (!storedCustomers || storedCustomers.length === 0) {
            customersDB = DEFAULT_CUSTOMERS;
            setStorage('customers', customersDB);
        } else {
            customersDB = storedCustomers;
        }

        ordersDB = getStorage('orders', []);
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

        // 3. Register Customer
        if ((cleanPath === '/api/customers/register' || cleanPath === '/api/customers') && method === 'POST') {
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
            return jsonRes({ message: 'Customer registered successfully!', customer: newCust });
        }

        // 4. Categories
        if (cleanPath === '/api/categories' && method === 'GET') {
            const cats = Array.from(new Set(productsDB.map(p => p.category)));
            return jsonRes(cats);
        }

        // 5. Products list (with optional ?q= & ?category= filtering)
        if (cleanPath.startsWith('/api/products') && method === 'GET') {
            const urlObj = new URL(u, window.location.origin);
            const q = (urlObj.searchParams.get('q') || '').toLowerCase().trim();
            const cat = urlObj.searchParams.get('category') || '';

            let result = productsDB;
            if (cat && cat !== 'All') {
                result = result.filter(p => p.category.toLowerCase() === cat.toLowerCase());
            }
            if (q) {
                result = result.filter(p => {
                    const matchName = p.name.toLowerCase().includes(q);
                    const matchCat = p.category.toLowerCase().includes(q);
                    const matchKeywords = (p.keywords || []).some(k => k.toLowerCase().includes(q));
                    return matchName || matchCat || matchKeywords;
                });
            }
            return jsonRes(result);
        }

        // 6. Add new product to catalogue (POST /api/products)
        if (cleanPath === '/api/products' && method === 'POST') {
            if (!body.name || !body.price || !body.category) {
                return jsonRes({ error: 'Missing required product fields (name, category, price)' }, 400);
            }
            const nextPid = 'P' + (100 + productsDB.length + 1);
            const newProd = {
                type: body.type || 'Electronics',
                product_id: nextPid,
                name: body.name.trim(),
                category: body.category.trim(),
                price: parseFloat(body.price),
                stock: parseInt(body.stock || 10, 10),
                image_url: body.image_url || 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=300&q=80',
                keywords: body.keywords || [body.name.toLowerCase()],
                discount_rate: parseFloat(body.discount_rate || 0.0),
                is_sellable: true,
                details: {}
            };
            productsDB.push(newProd);
            setStorage('products', productsDB);
            return jsonRes({ message: 'Product added to catalogue successfully!', product: newProd });
        }

        // 7. Cart view
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
                    line_total: line_total,
                    image_url: prod.image_url || ''
                };
            });
            return jsonRes({
                customer_id: customerId,
                items: items,
                total_items: total_items,
                subtotal: subtotal
            });
        }

        // 8. Cart Add
        if (cleanPath === '/api/cart/add' && method === 'POST') {
            if (!cartsDB[customerId]) cartsDB[customerId] = [];
            const prod = productsDB.find(p => p.product_id === body.product_id);
            if (!prod) return jsonRes({ error: 'Product not found' }, 400);
            const qty = parseInt(body.qty !== undefined ? body.qty : (body.quantity !== undefined ? body.quantity : 1), 10);
            if (qty <= 0) return jsonRes({ error: 'Quantity must be positive' }, 400);
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

        // 9. Cart Update
        if (cleanPath === '/api/cart/update' && method === 'POST') {
            if (!cartsDB[customerId]) cartsDB[customerId] = [];
            const prod = productsDB.find(p => p.product_id === body.product_id);
            const qty = parseInt(body.qty !== undefined ? body.qty : (body.quantity !== undefined ? body.quantity : 1), 10);
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

        // 10. Cart Remove (handles either decrement if qty provided or full removal)
        if (cleanPath === '/api/cart/remove' && method === 'POST') {
            if (cartsDB[customerId]) {
                const qtyToRemove = body.qty !== undefined ? parseInt(body.qty, 10) : (body.quantity !== undefined ? parseInt(body.quantity, 10) : null);
                if (qtyToRemove && qtyToRemove > 0) {
                    const existing = cartsDB[customerId].find(i => i.product_id === body.product_id);
                    if (existing) {
                        existing.quantity -= qtyToRemove;
                        if (existing.quantity <= 0) {
                            cartsDB[customerId] = cartsDB[customerId].filter(i => i.product_id !== body.product_id);
                        }
                    }
                } else {
                    cartsDB[customerId] = cartsDB[customerId].filter(i => i.product_id !== body.product_id);
                }
                setStorage('carts', cartsDB);
            }
            return jsonRes({ message: 'Item removed from cart' });
        }

        // 11. Cart Clear
        if (cleanPath === '/api/cart/clear' && method === 'POST') {
            cartsDB[customerId] = [];
            setStorage('carts', cartsDB);
            return jsonRes({ message: 'Cart cleared' });
        }

        // 12. Admin Stock Replenishment
        if (cleanPath === '/api/admin/stock' && method === 'POST') {
            const prod = productsDB.find(p => p.product_id === body.product_id);
            if (!prod) return jsonRes({ error: 'Product not found' }, 400);
            const qty = parseInt(body.qty || body.quantity || 0, 10);
            if (qty <= 0) return jsonRes({ error: 'Quantity must be positive' }, 400);

            prod.stock += qty;
            prod.is_sellable = true;
            setStorage('products', productsDB);
            return jsonRes({
                message: `Successfully added ${qty} units to ${prod.name}! New stock: ${prod.stock}`,
                product_id: prod.product_id,
                new_stock: prod.stock
            });
        }

        // 13. Checkout
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

        // 14. Orders
        if (cleanPath === '/api/orders' && method === 'GET') {
            const customerOrders = ordersDB.filter(o => o.customer_id === customerId);
            return jsonRes(customerOrders);
        }

        return originalFetch.apply(this, arguments);
    };
})();
