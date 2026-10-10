// SecureShop Lab Main Application Controller

let currentUser = null;
let currentProducts = [];
let cart = JSON.parse(localStorage.getItem("secureshop_cart") || "[]");
let currentSelectedProductId = null;
let isSecureMode = false;

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
    setupEventListeners();
    await checkAppHealth();
    await initAuth();
    loadCatalog();
    updateCartUI();
});

function setupEventListeners() {
    document.getElementById("btn-search").addEventListener("click", handleSearch);
    document.getElementById("global-search-input").addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSearch();
    });

    document.getElementById("btn-quick-toggle-mode").addEventListener("click", toggleModeQuick);

    window.addEventListener("auth-changed", (e) => {
        currentUser = e.detail;
        updateUserUI();
    });
}

// ============================================================================
// HEALTH & LAB MODE
// ============================================================================
async function checkAppHealth() {
    try {
        const health = await API.getHealth();
        setLabModeState(health.secure_mode);
    } catch (e) {
        console.warn("Backend not yet responding or starting up:", e);
    }
}

function setLabModeState(secureActive) {
    isSecureMode = secureActive;
    const banner = document.getElementById("lab-banner");
    const bannerText = document.getElementById("banner-text");

    if (secureActive) {
        banner.className = "lab-banner secure";
        bannerText.innerHTML = "CURRENT LAB STATUS: <strong>SECURE_MODE (HARDENED)</strong> — Defenses & Validations Enforced";
    } else {
        banner.className = "lab-banner vulnerable";
        bannerText.innerHTML = "CURRENT LAB STATUS: <strong>VULNERABLE TRAINING MODE</strong> — Educational Flaws Active";
    }
}

async function toggleModeQuick() {
    try {
        const res = await API.toggleSecureMode(!isSecureMode);
        setLabModeState(res.secure_mode);
        showToast(res.message, res.secure_mode ? "success" : "warning");
        if (document.getElementById("view-admin").classList.contains("active")) {
            refreshAdminDashboard();
        }
    } catch (err) {
        showToast(err.message || "Failed to toggle mode (requires admin session)", "error");
    }
}

// ============================================================================
// NAVIGATION
// ============================================================================
function navigateTo(viewName) {
    const views = ["catalog", "orders", "profile", "admin"];
    views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) {
            if (v === viewName) {
                el.classList.remove("hidden");
                el.classList.add("active");
            } else {
                el.classList.add("hidden");
                el.classList.remove("active");
            }
        }
    });

    // Update nav link active state
    document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = Array.from(document.querySelectorAll(".nav-btn")).find(b => b.textContent.toLowerCase().includes(viewName));
    if (activeBtn) activeBtn.classList.add("active");

    // Load view data
    if (viewName === "orders") loadOrders();
    if (viewName === "profile") loadProfile();
    if (viewName === "admin") refreshAdminDashboard();
}

// ============================================================================
// AUTHENTICATION
// ============================================================================
async function initAuth() {
    const token = API.getToken();
    if (!token) {
        updateUserUI();
        return;
    }
    try {
        currentUser = await API.getMe();
        updateUserUI();
    } catch (e) {
        API.setToken(null);
        currentUser = null;
        updateUserUI();
    }
}

function updateUserUI() {
    const loggedOutGroup = document.getElementById("auth-logged-out");
    const loggedInGroup = document.getElementById("auth-logged-in");
    const navAdminBtn = document.getElementById("nav-btn-admin");

    if (currentUser) {
        loggedOutGroup.classList.add("hidden");
        loggedInGroup.classList.remove("hidden");

        document.getElementById("nav-username").textContent = currentUser.username;
        document.getElementById("nav-role").textContent = currentUser.role.toUpperCase();
        if (currentUser.avatar_url) {
            document.getElementById("nav-avatar").src = currentUser.avatar_url;
        }

        // Show/hide admin nav button
        if (currentUser.role === "admin") {
            navAdminBtn.classList.remove("hidden");
        } else {
            navAdminBtn.classList.add("hidden");
        }
    } else {
        loggedOutGroup.classList.remove("hidden");
        loggedInGroup.classList.add("hidden");
        navAdminBtn.classList.add("hidden");
    }
}

function openAuthModal(tab = "login") {
    document.getElementById("modal-auth").classList.remove("hidden");
    switchAuthTab(tab);
}

function closeAuthModal() {
    document.getElementById("modal-auth").classList.add("hidden");
}

function switchAuthTab(tab) {
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const formLogin = document.getElementById("form-login");
    const formRegister = document.getElementById("form-register");

    if (tab === "login") {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
        formLogin.classList.remove("hidden");
        formRegister.classList.add("hidden");
    } else {
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
        formRegister.classList.remove("hidden");
        formLogin.classList.add("hidden");
    }
}

function fillCreds(username, password) {
    document.getElementById("login-username").value = username;
    document.getElementById("login-password").value = password;
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const u = document.getElementById("login-username").value.trim();
    const p = document.getElementById("login-password").value;

    try {
        const res = await API.login(u, p);
        API.setToken(res.token);
        currentUser = res.user;
        updateUserUI();
        closeAuthModal();
        showToast(`Welcome back, ${currentUser.username}!`, "success");
    } catch (err) {
        showToast(err.message || "Login failed", "error");
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const u = document.getElementById("reg-username").value.trim();
    const em = document.getElementById("reg-email").value.trim();
    const p = document.getElementById("reg-password").value;

    try {
        await API.register(u, em, p);
        showToast("Registration successful! Please log in.", "success");
        switchAuthTab("login");
        document.getElementById("login-username").value = u;
    } catch (err) {
        showToast(err.message || "Registration failed", "error");
    }
}

async function logout() {
    try {
        await API.logout();
    } catch (e) {}
    API.setToken(null);
    currentUser = null;
    updateUserUI();
    navigateTo("catalog");
    showToast("Signed out successfully", "success");
}

// ============================================================================
// CATALOG & PRODUCTS
// ============================================================================
async function loadCatalog(category = "") {
    const grid = document.getElementById("products-grid");
    grid.innerHTML = '<div class="loading-spinner">Loading catalog items...</div>';

    try {
        const products = await API.getProducts(category);
        currentProducts = products;
        renderProducts(products);
    } catch (err) {
        grid.innerHTML = `<div class="error-msg">Failed to load catalog: ${err.message}</div>`;
    }
}

function renderProducts(products) {
    const grid = document.getElementById("products-grid");
    if (!products || products.length === 0) {
        grid.innerHTML = '<div class="text-muted">No products found matching your criteria.</div>';
        return;
    }

    grid.innerHTML = products.map(p => `
        <div class="product-card" onclick="openProductModal(${p.id})">
            <div class="product-image-container">
                <span class="product-category-tag">${escapeHtml(p.category)}</span>
                <span style="font-size: 3.5rem;">🔒</span>
            </div>
            <div class="product-info">
                <h3 class="product-name">${escapeHtml(p.name)}</h3>
                <p class="product-description">${escapeHtml(p.description)}</p>
                <div class="product-card-footer" onclick="event.stopPropagation()">
                    <span class="product-price">$${p.price.toFixed(2)}</span>
                    <button class="btn btn-sm btn-outline" onclick="addToCart(${p.id}, 1)">Add to Cart</button>
                </div>
            </div>
        </div>
    `).join("");
}

function filterCategory(cat) {
    document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
    event.target.classList.add("active");
    loadCatalog(cat);
}

// LAB-002 (SQLi) & LAB-004 (Reflected XSS) Handler
async function handleSearch() {
    const query = document.getElementById("global-search-input").value.trim();
    if (!query) {
        clearSearchFilter();
        return;
    }

    const banner = document.getElementById("search-reflection-banner");
    const target = document.getElementById("reflection-target");
    banner.classList.remove("hidden");

    // LAB-004 Reflected XSS Demo:
    // If not secure mode, reflects input unescaped; in secure mode, escapes
    if (!isSecureMode) {
        // INTENTIONALLY VULNERABLE FOR LAB-004 (Reflected XSS)
        target.innerHTML = `Showing results for: ${query}`;
    } else {
        target.textContent = `Showing results for: ${query}`;
    }

    try {
        // LAB-002 SQL Injection search request
        const results = await API.searchProducts(query);
        currentProducts = results;
        renderProducts(results);
    } catch (err) {
        showToast(`Search error: ${err.message}`, "error");
    }
}

function clearSearchFilter() {
    document.getElementById("global-search-input").value = "";
    document.getElementById("search-reflection-banner").classList.add("hidden");
    loadCatalog();
}

// ============================================================================
// PRODUCT DETAIL & REVIEWS (LAB-003 Stored XSS)
// ============================================================================
async function openProductModal(productId) {
    currentSelectedProductId = productId;
    const modal = document.getElementById("modal-product-detail");
    modal.classList.remove("hidden");

    try {
        const product = await API.getProduct(productId);
        document.getElementById("modal-product-title").textContent = product.name;
        document.getElementById("modal-product-desc").textContent = product.description;
        document.getElementById("modal-product-price").textContent = `$${product.price.toFixed(2)}`;
        document.getElementById("modal-product-stock").textContent = `${product.stock} in stock`;
        document.getElementById("modal-product-category").textContent = product.category;

        renderReviews(product.reviews || []);
    } catch (err) {
        showToast(err.message, "error");
    }
}

function closeProductModal() {
    document.getElementById("modal-product-detail").classList.add("hidden");
    currentSelectedProductId = null;
}

function renderReviews(reviews) {
    const list = document.getElementById("modal-reviews-list");
    if (!reviews || reviews.length === 0) {
        list.innerHTML = '<p class="text-xs text-muted">No reviews yet. Be the first to leave feedback!</p>';
        return;
    }

    list.innerHTML = reviews.map(r => {
        // LAB-003 Stored XSS:
        // In vulnerable mode, renders raw comment string via innerHTML
        // In secure mode, text content is safe
        const commentHtml = isSecureMode ? escapeHtml(r.comment) : r.comment;
        return `
            <div class="review-item card" style="padding: 10px; margin-top: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <strong>${escapeHtml(r.username)}</strong>
                    <span>${"⭐".repeat(r.rating)}</span>
                </div>
                <div class="review-comment-body" style="font-size: 0.85rem; margin-top: 4px;">
                    ${commentHtml}
                </div>
            </div>
        `;
    }).join("");
}

async function submitProductReview() {
    if (!currentUser) {
        showToast("Please sign in to submit a product review", "warning");
        openAuthModal("login");
        return;
    }
    const rating = parseInt(document.getElementById("new-review-rating").value);
    const comment = document.getElementById("new-review-comment").value.trim();

    if (!comment) {
        showToast("Please enter a review comment", "warning");
        return;
    }

    try {
        await API.addReview(currentSelectedProductId, rating, comment);
        document.getElementById("new-review-comment").value = "";
        showToast("Review submitted successfully!", "success");
        // Reload reviews
        openProductModal(currentSelectedProductId);
    } catch (err) {
        showToast(err.message, "error");
    }
}

function addProductFromModal() {
    const qty = parseInt(document.getElementById("modal-add-qty").value) || 1;
    if (currentSelectedProductId) {
        addToCart(currentSelectedProductId, qty);
        closeProductModal();
    }
}

// ============================================================================
// SHOPPING CART & CHECKOUT (LAB-011 Logic Flaw)
// ============================================================================
function addToCart(productId, quantity = 1) {
    const prod = currentProducts.find(p => p.id === productId);
    if (!prod) return;

    const existing = cart.find(item => item.product_id === productId);
    if (existing) {
        existing.quantity += quantity;
    } else {
        cart.push({
            product_id: prod.id,
            product_name: prod.name,
            price: prod.price,
            quantity: quantity,
            client_price: null // In vulnerable mode, students can edit client price
        });
    }

    saveCart();
    updateCartUI();
    showToast(`Added ${prod.name} to cart`, "success");
}

function saveCart() {
    localStorage.setItem("secureshop_cart", JSON.stringify(cart));
}

function updateCartUI() {
    const badge = document.getElementById("cart-count-badge");
    const count = cart.reduce((acc, item) => acc + item.quantity, 0);
    badge.textContent = count;
}

function openCartModal() {
    renderCartModal();
    document.getElementById("modal-cart").classList.remove("hidden");
}

function closeCartModal() {
    document.getElementById("modal-cart").classList.add("hidden");
}

function renderCartModal() {
    const container = document.getElementById("cart-items-container");
    if (cart.length === 0) {
        container.innerHTML = '<p class="text-muted" style="padding: 20px 0;">Your cart is empty.</p>';
        document.getElementById("cart-total-amount").textContent = "$0.00";
        return;
    }

    container.innerHTML = cart.map((item, idx) => `
        <div class="cart-item-row" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border-color);">
            <div>
                <strong>${escapeHtml(item.product_name)}</strong>
                <div style="font-size: 0.8rem; color: var(--text-muted);">
                    Unit: $${item.price.toFixed(2)}
                    ${!isSecureMode ? `<span class="lab-pill text-xs">LAB-011 Logic Flaw: Editable Client Price/Qty</span>` : ''}
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <!-- Quantity Input: In vulnerable mode, accepts negative numbers! -->
                <input type="number" value="${item.quantity}" onchange="updateCartItemQty(${idx}, this.value)" class="input-xs" style="width: 60px;">
                ${!isSecureMode ? `
                    <input type="number" step="0.01" placeholder="Override $" value="${item.client_price || ''}" onchange="updateCartItemPrice(${idx}, this.value)" class="input-xs" title="Client price override (LAB-011)">
                ` : ''}
                <button class="btn btn-xs btn-outline-danger" onclick="removeFromCart(${idx})">✕</button>
            </div>
        </div>
    `).join("");

    calculateCartTotal();
}

function updateCartItemQty(idx, val) {
    cart[idx].quantity = parseInt(val) || 0;
    saveCart();
    renderCartModal();
    updateCartUI();
}

function updateCartItemPrice(idx, val) {
    cart[idx].client_price = val ? parseFloat(val) : null;
    saveCart();
    renderCartModal();
}

function removeFromCart(idx) {
    cart.splice(idx, 1);
    saveCart();
    renderCartModal();
    updateCartUI();
}

function clearCart() {
    cart = [];
    saveCart();
    renderCartModal();
    updateCartUI();
}

function calculateCartTotal() {
    let total = 0;
    for (const item of cart) {
        const p = item.client_price !== null && !isSecureMode ? item.client_price : item.price;
        total += p * item.quantity;
    }
    document.getElementById("cart-total-amount").textContent = `$${total.toFixed(2)}`;
    return total;
}

async function executeCheckout() {
    if (!currentUser) {
        showToast("Please sign in before checking out", "warning");
        openAuthModal("login");
        return;
    }

    if (cart.length === 0) {
        showToast("Cart is empty", "warning");
        return;
    }

    const shipping = document.getElementById("cart-shipping-input").value.trim();
    const coupon = document.getElementById("cart-coupon-input").value.trim() || null;

    const payloadItems = cart.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        client_price: !isSecureMode ? item.client_price : null
    }));

    try {
        const res = await API.checkout(payloadItems, shipping, coupon);
        showToast(`Order #${res.order_id} placed successfully! Total: $${res.total_amount}`, "success");
        clearCart();
        closeCartModal();
        navigateTo("orders");
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ============================================================================
// ORDERS & IDOR (LAB-001)
// ============================================================================
async function loadOrders() {
    if (!currentUser) {
        document.getElementById("orders-tbody").innerHTML = `<tr><td colspan="6" class="text-center">Please sign in to view your orders.</td></tr>`;
        return;
    }

    try {
        const orders = await API.getMyOrders();
        const tbody = document.getElementById("orders-tbody");

        if (orders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No orders placed yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td><strong>#${o.id}</strong></td>
                <td>${new Date(o.created_at).toLocaleDateString()}</td>
                <td><strong style="color: var(--accent-cyan);">$${o.total_amount.toFixed(2)}</strong></td>
                <td><span class="badge" style="background: var(--accent-emerald); color: #000;">${o.status.toUpperCase()}</span></td>
                <td>${escapeHtml(o.shipping_address)}</td>
                <td>
                    <button class="btn btn-xs btn-outline" onclick="inspectOrder(${o.id})">Details</button>
                    <button class="btn btn-xs btn-warning" onclick="downloadInvoiceForOrder(${o.id})">Invoice</button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        showToast(err.message, "error");
    }
}

// LAB-001 IDOR Test
async function testIdorOrder() {
    const orderId = document.getElementById("idor-order-id-input").value;
    inspectOrder(orderId);
}

async function inspectOrder(orderId) {
    try {
        const order = await API.getOrderById(orderId);
        alert(
            `=== ORDER #${order.id} DETAILS ===\n` +
            `User ID: ${order.user_id}\n` +
            `Total: $${order.total_amount}\n` +
            `Shipping Address: ${order.shipping_address}\n` +
            `Items: ${order.items.map(i => `${i.quantity}x ${i.product_name} ($${i.price})`).join(", ")}\n` +
            `Date: ${order.created_at}`
        );
    } catch (err) {
        showToast(`Authorization Check: ${err.message}`, "error");
    }
}

function downloadInvoiceForOrder(orderId) {
    navigateTo("profile");
    document.getElementById("traversal-filename-input").value = "invoice_sample.txt";
    downloadInvoiceFile();
}

// ============================================================================
// PROFILE & LAB EXPLOITATION CONSOLES
// ============================================================================
async function loadProfile() {
    if (!currentUser) {
        showToast("Please sign in to view your profile", "warning");
        openAuthModal("login");
        return;
    }

    try {
        const me = await API.getMe();
        currentUser = me;
        document.getElementById("profile-username").textContent = me.username;
        document.getElementById("profile-email").textContent = me.email;
        document.getElementById("profile-role-badge").textContent = me.role.toUpperCase();
        document.getElementById("profile-balance").textContent = `$${me.balance.toFixed(2)}`;
        if (me.avatar_url) {
            document.getElementById("profile-avatar-img").src = me.avatar_url;
        }

        const promoBtn = document.getElementById("btn-claim-promo");
        if (me.promo_claimed && isSecureMode) {
            promoBtn.disabled = true;
            promoBtn.textContent = "Claimed";
        } else {
            promoBtn.disabled = false;
            promoBtn.textContent = "Claim $50";
        }
    } catch (err) {
        showToast(err.message, "error");
    }
}

// LAB-006 Insecure File Upload
async function uploadAvatarFile() {
    const fileInput = document.getElementById("avatar-file-input");
    if (!fileInput.files || fileInput.files.length === 0) return;

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await API.uploadAvatar(formData);
        showToast(res.message, "success");
        document.getElementById("profile-avatar-img").src = res.avatar_url;
        document.getElementById("nav-avatar").src = res.avatar_url;
    } catch (err) {
        showToast(err.message, "error");
    }
}

// LAB-005 CSRF Demo
async function changeEmailCsrfDemo() {
    const email = document.getElementById("csrf-new-email").value.trim();
    if (!email) {
        showToast("Please specify a new email address", "warning");
        return;
    }

    try {
        const res = await API.changeEmailCsrf(email);
        showToast(res.message, "success");
        loadProfile();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// LAB-007 Path Traversal Invoice Download
async function downloadInvoiceFile() {
    const filename = document.getElementById("traversal-filename-input").value.trim();
    const preview = document.getElementById("traversal-output");

    try {
        const content = await API.downloadInvoice(filename);
        preview.textContent = content;
        preview.classList.remove("hidden");
        showToast(`Document retrieved successfully (${content.length} bytes)`, "success");
    } catch (err) {
        preview.textContent = `Error: ${err.message}`;
        preview.classList.remove("hidden");
        showToast(err.message, "error");
    }
}

// LAB-012 Race Condition Promo Claim
async function claimPromoCredit() {
    try {
        const res = await API.claimPromo("WELCOME50");
        showToast(res.message, "success");
        loadProfile();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// Simulate 5 simultaneous requests to trigger race condition (LAB-012)
async function testConcurrentRaceCondition() {
    showToast("Launching 5 concurrent promo claims...", "warning");
    const requests = [
        API.claimPromo("WELCOME50"),
        API.claimPromo("WELCOME50"),
        API.claimPromo("WELCOME50"),
        API.claimPromo("WELCOME50"),
        API.claimPromo("WELCOME50")
    ];

    const results = await Promise.allSettled(requests);
    const successes = results.filter(r => r.status === "fulfilled").length;
    const failures = results.filter(r => r.status === "rejected").length;

    showToast(`Race result: ${successes} claims succeeded, ${failures} rejected`, successes > 1 ? "warning" : "success");
    loadProfile();
}

// LAB-009 Password Reset Modal Handlers
function openForgotPasswordModal() {
    document.getElementById("modal-forgot-password").classList.remove("hidden");
}

function closeForgotPasswordModal() {
    document.getElementById("modal-forgot-password").classList.add("hidden");
}

async function requestPasswordResetToken() {
    const email = document.getElementById("forgot-email").value.trim();
    try {
        const res = await API.forgotPassword(email);
        const display = document.getElementById("reset-token-display-box");
        display.classList.remove("hidden");
        document.getElementById("display-reset-token").textContent = res.token || "Check simulated email";
        showToast(res.message, "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function executePasswordReset() {
    const token = document.getElementById("display-reset-token").textContent.trim();
    const newPass = document.getElementById("reset-new-password").value;

    try {
        const res = await API.resetPassword(token, newPass);
        showToast(res.message, "success");
        closeForgotPasswordModal();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ============================================================================
// ADMIN & SECURITY DASHBOARD
// ============================================================================
async function refreshAdminDashboard() {
    if (!currentUser || currentUser.role !== "admin") {
        document.getElementById("metric-users").textContent = "-";
        return;
    }

    try {
        const data = await API.getAdminMetrics();
        document.getElementById("metric-users").textContent = data.metrics.total_users;
        document.getElementById("metric-orders").textContent = data.metrics.total_orders;
        document.getElementById("metric-login-success").textContent = data.metrics.login_success_count;
        document.getElementById("metric-login-failure").textContent = data.metrics.login_failure_count;

        setLabModeState(data.secure_mode_enabled);

        renderVulnerabilityMatrix(data.vulnerabilities || []);
        loadAuditLogs();
        loadAdminUsers();
    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderVulnerabilityMatrix(matrix) {
    const tbody = document.getElementById("vulnerability-matrix-tbody");
    tbody.innerHTML = matrix.map(v => {
        const isVuln = v.status === "VULNERABLE";
        const badgeColor = isVuln ? "var(--accent-amber)" : "var(--accent-emerald)";
        return `
            <tr>
                <td><span class="lab-pill">${v.id}</span></td>
                <td><strong>${escapeHtml(v.name)}</strong></td>
                <td><span class="badge" style="background: rgba(255,255,255,0.06); color: var(--text-secondary);">${v.category}</span></td>
                <td><span class="badge" style="background: ${badgeColor}; color: #000;">${v.status}</span></td>
                <td><code style="font-size: 0.75rem; color: var(--accent-cyan); font-family: var(--font-mono);">${getVulnerabilityEndpoint(v.id)}</code></td>
                <td><button class="btn btn-xs btn-outline" onclick="openLabDetails('${v.id}')">Inspect Guide</button></td>
            </tr>
        `;
    }).join("");
}

function getVulnerabilityEndpoint(id) {
    const endpoints = {
        "LAB-001": "GET /api/orders/{id}",
        "LAB-002": "GET /api/products/search?q=",
        "LAB-003": "POST /api/products/{id}/reviews",
        "LAB-004": "GET /api/products/search-echo",
        "LAB-005": "POST /api/users/csrf-change-email",
        "LAB-006": "POST /api/users/upload-avatar",
        "LAB-007": "GET /api/orders/download/invoice",
        "LAB-008": "POST /api/admin/import-webhook",
        "LAB-009": "POST /api/auth/login (missing rate limit)",
        "LAB-010": "Session Cookie / Session Store",
        "LAB-011": "POST /api/cart/checkout",
        "LAB-012": "POST /api/cart/claim-promo"
    };
    return endpoints[id] || "/api/...";
}

function openLabDetails(labId) {
    alert(`Please refer to the documentation file:\n\ndocs/vulnerabilities/${labId}.md\n\nContains root cause analysis, reproduction steps, secure remediation, code examples, and automated tests.`);
}

async function loadAuditLogs() {
    try {
        const logs = await API.getAdminLogs(30);
        const tbody = document.getElementById("audit-logs-tbody");
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No logs recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td style="font-family: var(--font-mono); font-size: 0.75rem;">${new Date(l.created_at).toLocaleTimeString()}</td>
                <td><span class="lab-pill" style="font-size: 0.68rem;">${l.event_type}</span></td>
                <td><strong>${escapeHtml(l.username || 'anon')}</strong></td>
                <td style="font-family: var(--font-mono); font-size: 0.75rem;">${l.ip_address}</td>
                <td style="font-size: 0.8rem; color: var(--text-secondary);">${escapeHtml(l.details)}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Failed to load audit logs:", e);
    }
}

async function loadAdminUsers() {
    try {
        const users = await API.getAdminUsers();
        const tbody = document.getElementById("admin-users-tbody");
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>#${u.id}</td>
                <td><strong>${escapeHtml(u.username)}</strong></td>
                <td>${escapeHtml(u.email)}</td>
                <td><span class="badge" style="background: ${u.role === 'admin' ? 'var(--accent-amber)' : 'var(--accent-blue)'}; color: #000;">${u.role.toUpperCase()}</span></td>
                <td>$${u.balance.toFixed(2)}</td>
                <td>${u.promo_claimed ? 'Yes' : 'No'}</td>
                <td>
                    <button class="btn btn-xs btn-outline" onclick="toggleUserRole(${u.id}, '${u.role === 'admin' ? 'user' : 'admin'}')">
                        Make ${u.role === 'admin' ? 'User' : 'Admin'}
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Failed to load admin users:", e);
    }
}

async function toggleUserRole(userId, newRole) {
    try {
        await API.setUserRole(userId, newRole);
        showToast(`Role updated to ${newRole}`, "success");
        loadAdminUsers();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// LAB-008 SSRF Console Actions
function applySsrfPreset() {
    const val = document.getElementById("ssrf-preset-select").value;
    document.getElementById("ssrf-target-url").value = val;
}

async function triggerSsrfRequest() {
    const url = document.getElementById("ssrf-target-url").value.trim();
    const output = document.getElementById("ssrf-response-output");
    output.textContent = "Sending webhook request to target...";

    try {
        const res = await API.importWebhookSSRF(url);
        output.textContent = JSON.stringify(res, null, 2);
        showToast("SSRF fetch completed!", "success");
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
        showToast(err.message, "error");
    }
}

async function toggleSecureModeFromAdmin() {
    await toggleModeQuick();
}

// ============================================================================
// UTILITIES
// ============================================================================
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4500);
}

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
