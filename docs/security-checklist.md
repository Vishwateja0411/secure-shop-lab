# SecureShop Lab — Security Architecture Checklist

A comprehensive production-grade checklist across 15 security domains covering software engineering, systems administration, and cloud deployment.

---

## 1. Authentication
- [ ] Enforce strong password complexity (minimum 8 characters, uppercase, lowercase, numbers, and symbols).
- [ ] Implement salted, adaptive password hashing algorithms (Bcrypt with work factor >= 12 or Argon2id).
- [ ] Implement account lockout or progressive rate limiting on login endpoints (e.g. max 5 failed attempts per minute).
- [ ] Avoid username enumeration in authentication responses (use uniform error messages such as "Invalid username or password").
- [ ] Protect password reset flows with cryptographically random tokens (256-bit entropy) with short expiration windows (<= 15 minutes) and single-use invalidation.

## 2. Authorization
- [ ] Enforce Object-Level Access Control (IDOR prevention) on all entity retrievals by verifying that the authenticated user owns the resource or has administrative rights.
- [ ] Implement Function-Level Access Control (RBAC/ABAC) on every sensitive endpoint.
- [ ] Never rely on client-supplied headers (e.g. `X-Admin-Role`) to bypass authorization logic.
- [ ] Reject requests with HTTP 403 Forbidden when authorization fails, and record an audit log event.

## 3. Session Management
- [ ] Issue high-entropy, cryptographically random session tokens (e.g. `secrets.token_urlsafe(32)`).
- [ ] Set cookie security attributes: `HttpOnly` (blocks JavaScript access), `SameSite=Lax` or `Strict` (mitigates CSRF), and `Secure` (requires HTTPS).
- [ ] Maintain server-side session stores with absolute expiration (TTL) and idle timeouts.
- [ ] Invalidate session tokens immediately on logout or password changes.

## 4. Input Validation
- [ ] Validate all inputs on the server side using strict schemas (e.g. Pydantic, schema validators).
- [ ] Enforce type, length, format, and numerical range constraints (e.g. `quantity > 0`).
- [ ] Validate file upload parameters, query strings, headers, and body payloads against allowlists.
- [ ] Reject unexpected or extra fields in incoming payloads.

## 5. Output Encoding
- [ ] Encode untrusted data prior to rendering in HTML contexts using contextual encoding (HTML entities: `&`, `<`, `>`, `"`, `'`).
- [ ] Use modern client frameworks or native `textContent` DOM properties instead of unsafe sinks like `innerHTML`.
- [ ] Ensure API responses set accurate `Content-Type` headers (e.g. `application/json; charset=utf-8`).

## 6. Database Security
- [ ] Use parameterized queries, prepared statements, or modern ORMs for all database interactions.
- [ ] Never concatenate raw user input into dynamic SQL strings.
- [ ] Apply the principle of least privilege to database users (e.g. grant only necessary `SELECT`, `INSERT`, `UPDATE`, `DELETE` permissions).
- [ ] Prevent race conditions during transactional updates using atomic SQL statements (`UPDATE ... WHERE condition RETURNING id`) or `SELECT ... FOR UPDATE` row locks.

## 7. API Security
- [ ] Validate and sanitize all API path parameters, query parameters, and JSON payloads.
- [ ] Implement anti-CSRF protections (e.g. custom headers like `X-CSRF-Token` or synchronizer tokens) for state-changing browser requests.
- [ ] Configure restrictive Cross-Origin Resource Sharing (CORS) allowlists without wildcard `*` when credentials are permitted.
- [ ] Return standardized, non-verbose error responses without leaking stack traces or internal software versions.

## 8. File Upload Security
- [ ] Restrict permitted file extensions to an explicit whitelist (e.g. `.png`, `.jpg`, `.jpeg`, `.webp`).
- [ ] Validate file MIME types and inspect file header magic bytes on the server.
- [ ] Generate randomized unique filenames (e.g. `uuid4().hex + ext`) to prevent directory traversal and file overwriting.
- [ ] Enforce strict file size limits (e.g. max 2MB).
- [ ] Store files outside the web root or disable execution permissions on the upload directory.

## 9. Browser Security & Security Headers
- [ ] Set `Content-Security-Policy` (CSP) to restrict scripts, styles, fonts, and frame ancestors.
- [ ] Set `X-Frame-Options: DENY` to prevent clickjacking attacks.
- [ ] Set `X-Content-Type-Options: nosniff` to prevent MIME confusion attacks.
- [ ] Set `Referrer-Policy: strict-origin-when-cross-origin` to prevent URL leakage.
- [ ] Set `Strict-Transport-Security` (HSTS) in production environments.

## 10. Secrets Management
- [ ] Never commit passwords, API keys, or private certificates into version control.
- [ ] Supply configuration secrets through environment variables or secure secret managers.
- [ ] Store `.env` files outside version control and maintain a sanitized `.env.example`.
- [ ] Regularly rotate production cryptographic keys.

## 11. Logging & Monitoring
- [ ] Implement structured logging (e.g. JSON format) capturing security events: auth successes, auth failures, logouts, role changes, file uploads, and errors.
- [ ] Automatically redact sensitive data (passwords, tokens, credit cards) before writing to logs.
- [ ] Include context metadata in logs: timestamp, event type, username, and client IP.
- [ ] Monitor logs for abnormal frequency of failed logins or unauthorized requests.

## 12. Docker Security
- [ ] Use minimal, hardened base images (e.g. `alpine` or `python:3.11-slim`).
- [ ] Avoid running containers as the root user in production.
- [ ] Define resource constraints (memory, CPU limits) to mitigate container denial-of-service.
- [ ] Use separate internal Docker bridge networks to restrict inter-container traffic.

## 13. Nginx Reverse Proxy Security
- [ ] Enforce `client_max_body_size` (e.g. 10M) to block oversized payload attacks.
- [ ] Hide Nginx server version tokens (`server_tokens off;`).
- [ ] Route only explicit endpoints (`/api/`, `/uploads/`) to backend services.
- [ ] Configure rate limiting zones on Nginx for public endpoints.

## 14. PostgreSQL Security
- [ ] Do not expose port 5432 to the public internet; bind strictly to internal container networks.
- [ ] Use strong passwords for database users.
- [ ] Enable SSL connections between the backend application and the database in distributed setups.
- [ ] Perform regular automated database backups and test recovery procedures.

## 15. CI/CD & DevSecOps Security
- [ ] Run automated unit and security regression test suites on every pull request.
- [ ] Integrate Static Application Security Testing (SAST) tools (such as Bandit or Semgrep) into CI pipelines.
- [ ] Scan dependencies for known vulnerabilities (CVEs) using scanners like Safety or Pip-audit.
- [ ] Perform automated secret scanning (e.g. TruffleHog or Detect-secrets) to block accidental credential leaks.
