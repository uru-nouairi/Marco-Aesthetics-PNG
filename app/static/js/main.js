document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;

    if (path.includes('/login')) {
        initLoginPage();
    } else if (path.includes('/admin')) {
        initAdminDashboard();
    } else if (path.includes('/cashier')) {
        initCashierDashboard();
    }
});

function initLoginPage() {
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = form.username.value;
        const password = form.password.value;
        const errorMessage = document.getElementById('error-message');

        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        if (data.success) {
            window.location.href = data.role === 'admin' ? '/admin' : '/cashier';
        } else {
            errorMessage.textContent = data.message;
        }
    });
}

function initAdminDashboard() {
    const productList = document.getElementById('product-list');
    const productForm = document.getElementById('product-form');
    const productIdField = document.getElementById('product-id');
    const productNameField = document.getElementById('product-name');
    const productPriceField = document.getElementById('product-price');
    const productStockField = document.getElementById('product-stock');

    async function fetchProducts() {
        const response = await fetch('/api/products');
        const products = await response.json();
        productList.innerHTML = '';
        products.forEach(p => {
            const item = document.createElement('div');
            item.innerHTML = `
                <span>${p.name} - K${p.price} (Stock: ${p.stock})</span>
                <button onclick="editProduct(${p.id}, '${p.name}', ${p.price}, ${p.stock})">Edit</button>
                <button onclick="deleteProduct(${p.id})">Delete</button>
            `;
            productList.appendChild(item);
        });
    }

    productForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = productIdField.value;
        const productData = {
            name: productNameField.value,
            price: parseFloat(productPriceField.value),
            stock_quantity: parseInt(productStockField.value)
        };

        const url = id ? `/api/products/${id}` : '/api/products';
        const method = id ? 'PUT' : 'POST';

        await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });

        productForm.reset();
        productIdField.value = '';
        fetchProducts();
    });

    window.editProduct = (id, name, price, stock) => {
        productIdField.value = id;
        productNameField.value = name;
        productPriceField.value = price;
        productStockField.value = stock;
    };

    window.deleteProduct = async (id) => {
        if (confirm('Are you sure you want to delete this product?')) {
            await fetch(`/api/products/${id}`, { method: 'DELETE' });
            fetchProducts();
        }
    };

    fetchProducts();
}

function initCashierDashboard() {
    const productGrid = document.getElementById('product-grid');
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const processSaleBtn = document.getElementById('process-sale-btn');
    const receiptLinkContainer = document.getElementById('receipt-link-container');
    let cart = [];

    async function fetchProducts() {
        const response = await fetch('/api/products');
        const products = await response.json();
        productGrid.innerHTML = '';
        products.forEach(p => {
            const item = document.createElement('div');
            item.className = 'product-item';
            item.innerHTML = `<strong>${p.name}</strong><br>K${p.price}`;
            item.onclick = () => addToCart(p);
            productGrid.appendChild(item);
        });
    }

    function addToCart(product) {
        const existingItem = cart.find(item => item.id === product.id);
        if (existingItem) {
            existingItem.quantity++;
        } else {
            cart.push({ ...product, quantity: 1 });
        }
        renderCart();
    }

    function renderCart() {
        cartItems.innerHTML = '';
        let total = 0;
        cart.forEach(item => {
            const cartItem = document.createElement('div');
            cartItem.className = 'cart-item';
            cartItem.innerHTML = `
                <span>${item.name} x ${item.quantity}</span>
                <span>K${(item.price * item.quantity).toFixed(2)}</span>
            `;
            cartItems.appendChild(cartItem);
            total += item.price * item.quantity;
        });
        cartTotal.textContent = total.toFixed(2);
    }

    processSaleBtn.addEventListener('click', async () => {
        if (cart.length === 0) {
            alert('Cart is empty.');
            return;
        }

        const response = await fetch('/api/sales', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cart: cart.map(i => ({id: i.id, quantity: i.quantity})) })
        });

        const data = await response.json();
        if (data.success) {
            alert('Sale processed successfully!');
            receiptLinkContainer.innerHTML =
                `<a href="/api/receipt/${data.sale_id}" target="_blank">View Receipt</a>`;
            cart = [];
            renderCart();
            fetchProducts();
        } else {
            alert(`Error: ${data.message}`);
            receiptLinkContainer.innerHTML = '';
        }
    });

    fetchProducts();
}
