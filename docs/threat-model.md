# SecureShop Lab — Threat Model

This document outlines the application security threat model for **SecureShop Lab** using the STRIDE methodology and industry standard threat modeling principles.

---

## 1. ASCII Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                              UNTRUSTED ZONE (INTERNET)                             |
|                                                                                   |
|    [ Attacker / Student ]                      [ Legitimate Customer / Admin ]     |
|              |                                                |                   |
|              +-----------------------+------------------------+                   |
+--------------------------------------|--------------------------------------------+
                                       | HTTP (Port 80)
                                       v
+-----------------------------------------------------------------------------------+
|                        DMZ / REVERSE PROXY BOUNDARY                               |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | NGINX REVERSE PROXY (:80)                                                    |  |
|  |  - Serves Static SPA Frontend (/usr/share/nginx/html)                        |  |
|  |  - Reverse Proxies /api/* to Backend (:8000)                                |  |
|  |  - Reverse Proxies /uploads/* to Static Asset Storage                        |  |
|  |  - Enforces Client Max Body Size (10MB) & SSL/TLS Termination               |  |
|  +-----------------------------------------------------------------------------+  |
+--------------------------------------|--------------------------------------------+
                                       | Internal Docker Bridge Network
                                       v
+-----------------------------------------------------------------------------------+
|                         APPLICATION RUNTIME BOUNDARY                              |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | FASTAPI BACKEND SERVICE (:8000)                                             |  |
|  |                                                                             |  |
|  |   [Auth & RBAC]         [Cart & Checkout]        [Admin Dashboard]          |  |
|  |   - Login / Register    - Price & Quantity Calc  - Metrics & Log Viewer     |  |
|  |   - Password Reset      - Concurrency / Promo    - SSRF Webhook Client      |  |
|  |                                                                             |  |
|  |   [Products & Reviews]  [Orders & Invoices]      [Profile & Avatars]        |  |
|  |   - Search (SQL Filter) - Order History (IDOR)   - File Uploads             |  |
|  |   - User Feedback (XSS) - Traversal / Invoices   - CSRF Email Update        |  |
|  |                                                                             |  |
|  |   [Security Subsystem: SECURE_MODE Switch]                                  |  |
|  |   - Parameterized SQL   - CSP & Security Headers - Safe Canonicalization    |  |
|  |   - Rate Limiter        - Strict SSRF Allowlist  - Row-Level DB Locking     |  |
|  +-----------------------------------------------------------------------------+  |
|                         |                                  |                      |
|                         | File I/O                         | SQL Protocol (:5432) |
|                         v                                  v                      |
|  +-------------------------------+         +-----------------------------------+  |
|  | PERSISTENT FILE STORAGE       |         | POSTGRESQL DATABASE (:5432)       |  |
|  |  - /app/uploads/ (Avatars)    |         |  - users (hashes, roles, balance) |  |
|  |  - /app/invoices/ (Receipts)  |         |  - products, orders, reviews      |  |
|  |                               |         |  - coupons, audit_logs            |  |
|  +-------------------------------+         +-----------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Assets

1. **User Identity & Credentials**: Passwords, password reset tokens, session identifiers.
2. **Personal Identifiable Information (PII)**: User full names, physical delivery addresses, emails.
3. **Financial & Order Records**: Order histories, item costs, user balances, promotional coupons.
4. **Server Filesystem & Configuration**: Source code files, `.env` application secrets, database credentials.
5. **Database Records**: Relational tables in PostgreSQL containing customer and administrative data.
6. **Internal Network / Services**: Internal Docker services, mock secret vault, administrative endpoints.

---

## 3. Threat Actors

| Actor | Access Level | Motivation | Capabilities |
| :--- | :--- | :--- | :--- |
| **Anonymous Attacker** | External Internet / Unauthenticated | Unauthorized data acquisition, account takeover | Automated scanners, fuzzers, CSRF campaigns |
| **Malicious Authenticated User** | Standard Customer Account | Privilege escalation, financial manipulation, fraud | IDOR probing, race condition concurrency, stored XSS |
| **Compromised Insider / Admin** | Administrative Portal | Data exfiltration, denial of service | Accessing audit logs, invoking SSRF webhooks |

---

## 4. Trust Boundaries

1. **Boundary A (Browser ↔ Nginx)**: Separates untrusted public client traffic from the reverse proxy DMZ.
2. **Boundary B (Nginx ↔ FastAPI)**: Internal Docker bridge passing parsed HTTP traffic into the application logic.
3. **Boundary C (FastAPI ↔ PostgreSQL)**: Application layer executing SQL queries over TCP socket against database engine.
4. **Boundary D (FastAPI ↔ Local Filesystem)**: Application writing uploaded images and reading invoice documents on disk.
5. **Boundary E (FastAPI ↔ Internal Microservices)**: HTTP requests initiated by FastAPI to external or internal URLs (SSRF boundary).

---

## 5. Entry Points & Attack Surface

- `POST /api/auth/register`, `POST /api/auth/login`: Authentication credential input.
- `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`: Password reset flows.
- `GET /api/products/search`: Query parameter input searching catalog.
- `GET /api/products/search-echo`: Query reflection into response body.
- `POST /api/products/{id}/reviews`: Persistent comment submissions.
- `POST /api/cart/checkout`: Client-supplied JSON payload containing item IDs, quantities, prices, and coupon codes.
- `POST /api/cart/claim-promo`: Concurrency-sensitive endpoint awarding credit.
- `GET /api/orders/{id}`: Object reference parameter retrieving order metadata.
- `GET /api/orders/download/invoice`: File path query parameter retrieving invoices.
- `POST /api/users/upload-avatar`: Multipart file upload accepting user files.
- `POST /api/users/csrf-change-email`: State-changing form modifying user email.
- `POST /api/admin/import-webhook`: URL parameter commanding server to perform HTTP GET (SSRF).

---

## 6. STRIDE Threat Analysis & Mitigations

| Threat Category | Potential Impact | Insecure Lab Flaw | Secure Mode Mitigation |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Attacker impersonates legitimate user or admin | Weak session token generation (`LAB-010`), forged `X-Admin-Override` header (`LAB-001`) | 256-bit cryptographically random tokens, server-side session TTL, verified database roles |
| **Tampering** | Attacker alters prices or orders | Client-side price override, negative quantities (`LAB-011`), race conditions (`LAB-012`) | Server-side price recalculation from database records, validation checks (`qty > 0`), atomic transactions |
| **Repudiation** | Attacker denies malicious actions | Unstructured or missing security logging | Centralized structured audit logs recording auth successes, auth failures, uploads, and admin actions with secrets redacted |
| **Information Disclosure** | Leakage of PII, source code, or internal tokens | IDOR on orders (`LAB-001`), Path traversal (`LAB-007`), SSRF to mock vault (`LAB-008`), verbose stack traces | Object-level authorization checks, path canonicalization (`realpath`), SSRF domain allowlists, generic error responses |
| **Denial of Service** | Exhaustion of server resources or authentication locks | Missing rate limiting on login (`LAB-009`), unconstrained file uploads (`LAB-006`) | In-memory IP rate limiting (5 attempts/min), 2MB file size limits, request timeouts |
| **Elevation of Privilege** | Standard user obtains administrative rights | Bypassing RBAC checks via custom headers or insecure session crafting | Strict RBAC dependency checking user role in database, session authentication verification |

---

## 7. Security Assumptions

1. The host operating system running Docker Compose is physically secure.
2. Database credentials in `.env` are protected by local file permissions on production systems.
3. Network isolation provided by Docker bridge networks prevents unauthorized external access to the database container directly.
