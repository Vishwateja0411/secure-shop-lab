// SecureShop Lab API Client
const API_BASE = ""; // Relative to host (handled by Nginx reverse proxy or direct host)

const API = {
    getToken() {
        return localStorage.getItem("secureshop_token") || "";
    },

    setToken(token) {
        if (token) {
            localStorage.setItem("secureshop_token", token);
        } else {
            localStorage.removeItem("secureshop_token");
        }
    },

    async request(endpoint, options = {}) {
        const headers = options.headers || {};
        const token = this.getToken();

        if (token && !headers["Authorization"]) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        if (!options.isFormData && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }

        const config = {
            ...options,
            headers
        };

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, config);
            
            // Check if 401 unauth
            if (res.status === 401 && !endpoint.includes("/auth/login")) {
                this.setToken(null);
                window.dispatchEvent(new CustomEvent("auth-changed", { detail: null }));
            }

            const contentType = res.headers.get("content-type");
            let data;
            if (contentType && contentType.includes("application/json")) {
                data = await res.json();
            } else {
                data = await res.text();
            }

            if (!res.ok) {
                const errorMsg = (typeof data === "object" && (data.detail || data.message)) || data || `Request failed with status ${res.status}`;
                throw new Error(errorMsg);
            }

            return data;
        } catch (err) {
            console.error(`API Error on ${endpoint}:`, err);
            throw err;
        }
    },

    // Auth
    login(username, password) {
        return this.request("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });
    },

    register(username, email, password) {
        return this.request("/api/auth/register", {
            method: "POST",
            body: JSON.stringify({ username, email, password })
        });
    },

    logout() {
        return this.request("/api/auth/logout", { method: "POST" });
    },

    getMe() {
        return this.request("/api/auth/me");
    },

    forgotPassword(email) {
        return this.request("/api/auth/forgot-password", {
            method: "POST",
            body: JSON.stringify({ email })
        });
    },

    resetPassword(token, new_password) {
        return this.request("/api/auth/reset-password", {
            method: "POST",
            body: JSON.stringify({ token, new_password })
        });
    },

    // Products
    getProducts(category = "") {
        const query = category ? `?category=${encodeURIComponent(category)}` : "";
        return this.request(`/api/products${query}`);
    },

    getProduct(id) {
        return this.request(`/api/products/${id}`);
    },

    searchProducts(q) {
        return this.request(`/api/products/search?q=${encodeURIComponent(q)}`);
    },

    searchEcho(query) {
        return this.request(`/api/products/search-echo?query=${encodeURIComponent(query)}`);
    },

    addReview(productId, rating, comment) {
        return this.request(`/api/products/${productId}/reviews`, {
            method: "POST",
            body: JSON.stringify({ rating, comment })
        });
    },

    // Cart & Checkout
    checkout(items, shipping_address, coupon_code) {
        return this.request("/api/cart/checkout", {
            method: "POST",
            body: JSON.stringify({ items, shipping_address, coupon_code })
        });
    },

    claimPromo(promo_code = "WELCOME50") {
        return this.request("/api/cart/claim-promo", {
            method: "POST",
            body: JSON.stringify({ promo_code })
        });
    },

    // Orders
    getMyOrders() {
        return this.request("/api/orders");
    },

    getOrderById(id) {
        return this.request(`/api/orders/${id}`);
    },

    downloadInvoice(filename) {
        return this.request(`/api/orders/download/invoice?filename=${encodeURIComponent(filename)}`);
    },

    // Users
    getUserProfile(userId) {
        return this.request(`/api/users/profile/${userId}`);
    },

    uploadAvatar(formData) {
        return this.request("/api/users/upload-avatar", {
            method: "POST",
            body: formData,
            isFormData: true
        });
    },

    changeEmailCsrf(email) {
        const formBody = new URLSearchParams();
        formBody.append("email", email);
        return this.request("/api/users/csrf-change-email", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formBody.toString()
        });
    },

    // Admin & Dashboard
    getAdminMetrics() {
        return this.request("/api/admin/metrics");
    },

    getAdminLogs(limit = 50) {
        return this.request(`/api/admin/logs?limit=${limit}`);
    },

    getAdminUsers() {
        return this.request("/api/admin/users");
    },

    setUserRole(userId, role) {
        return this.request(`/api/admin/users/${userId}/role`, {
            method: "POST",
            body: JSON.stringify({ role })
        });
    },

    importWebhookSSRF(url) {
        return this.request("/api/admin/import-webhook", {
            method: "POST",
            body: JSON.stringify({ webhook_url: url })
        });
    },

    toggleSecureMode(enable) {
        return this.request("/api/admin/toggle-secure-mode", {
            method: "POST",
            body: JSON.stringify({ enable_secure_mode: enable })
        });
    },

    getHealth() {
        return this.request("/api/health");
    }
};
