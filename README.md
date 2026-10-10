# SecureShop Lab — Vulnerable Web Application Security Lab

[![Security CI](https://github.com/secureshop/secureshop-lab/actions/workflows/security-ci.yml/badge.svg)](https://github.com/secureshop/secureshop-lab/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)

> **IMPORTANT SECURITY NOTICE**:
> **SecureShop Lab is a deliberately vulnerable web application designed exclusively for educational purposes**, Application Security training, secure coding instruction, threat modeling, and defensive engineering.
>
> - **Self-Contained & Local-Only**: The lab operates exclusively on your local machine (`127.0.0.1` / `localhost`).
> - **No External Connections**: The lab does not connect to or attack external systems.
> - **Safe Educational Boundaries**: Features such as SSRF and SQL injection are confined to local mock services and sandboxed database tables.

---

## 1. Requirements

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/) (v2.0+)
- Alternatively for direct host execution:
  - Python 3.11+
  - PostgreSQL 16 (or local SQLite fallback included)

---

## 2. Technology Stack & Architecture

- **Frontend**: HTML5, Vanilla CSS (Dark Cyber Theme), Vanilla JavaScript (SPA Controller)
- **Reverse Proxy**: Nginx (Alpine)
- **Backend API**: Python 3.11 + FastAPI + Pydantic v2
- **Database Engine**: PostgreSQL 16 (Alpine) + SQLAlchemy 2.0
- **Testing & QA**: pytest + pytest-asyncio + Starlette TestClient

```
Internet / Browser
       │
       ▼ (Port 80)
┌──────────────┐
│    Nginx     │  (Reverse proxy, static SPA hosting, rate limits)
└──────┬───────┘
       │
       ▼ (Port 8000)
┌──────────────┐
│   FastAPI    │  (Authentication, Business logic, REST API, Auditing)
└──────┬───────┘
       │
       ▼ (Port 5432)
┌──────────────┐
│  PostgreSQL  │  (Relational schema, seed data, persistent volumes)
└──────────────┘
```

---

## 3. Quick Start Commands

### Starting the Vulnerable Lab (Default Training Mode)
```bash
docker compose up --build
```
The application will be accessible at:
- **Web Application & UI**: [http://localhost](http://localhost)
- **Direct Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Reference**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Starting Secure Mode (Hardened Defenses Active)
Edit `.env` (or toggle directly from the Admin Security Dashboard):
```env
SECURE_MODE=true
```
Then restart the containers:
```bash
docker compose up -d
```

### Stopping the Lab
```bash
docker compose down
```

### Resetting the Database & Uploads
```bash
docker compose down -v
```

### Running Automated Security Tests
```bash
# Inside the backend container or locally:
pytest
```

---

## 4. Default Demo Accounts

On startup, the database is pre-seeded with realistic demo accounts:

| Username | Email | Password | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`admin`** | `admin@secureshop.lab` | `AdminPass123!` | `admin` | Administrator & Security Lead |
| **`alice`** | `alice@secureshop.lab` | `AlicePass123!` | `user` | Security Engineer (Owns Order #1) |
| **`bob`** | `bob@secureshop.lab` | `BobPass123!` | `user` | QA Engineer (Owns Order #2) |

---

## 5. Vulnerability Matrix (LAB-001 through LAB-012)

| ID | Vulnerability | Location | Secure Fix | Test File |
| :--- | :--- | :--- | :--- | :--- |
| **LAB-001** | Broken Access Control (IDOR) | `backend/app/api/orders.py:46` | Enforce object ownership checks (`current_user.id == order.user_id`) | `test_lab001_idor.py` |
| **LAB-002** | SQL Injection | `backend/app/api/products.py:42` | Parameterized ORM queries with bound parameters | `test_lab002_sqli.py` |
| **LAB-003** | Stored XSS | `backend/app/api/products.py:143` | Input HTML entity encoding & safe `textContent` DOM binding | `test_lab003_stored_xss.py` |
| **LAB-004** | Reflected XSS | `backend/app/api/products.py:101` | Contextual output encoding & Content-Security-Policy | `test_lab004_reflected_xss.py` |
| **LAB-005** | CSRF | `backend/app/api/users.py:137` | Anti-CSRF token verification (`X-CSRF-Token`) & `SameSite=Lax` cookies | `test_lab005_csrf.py` |
| **LAB-006** | Insecure File Upload | `backend/app/api/users.py:73` | Extension whitelist (`.png`, `.jpg`), MIME validation, UUID filenames | `test_lab006_file_upload.py` |
| **LAB-007** | Path Traversal | `backend/app/api/orders.py:88` | Canonical path resolution (`os.path.realpath`) & boundary verification | `test_lab007_path_traversal.py` |
| **LAB-008** | SSRF (Local Sandbox) | `backend/app/api/admin.py:97` | Strict allowlist restricting requests to approved public mock catalog | `test_lab008_ssrf.py` |
| **LAB-009** | Weak Authentication & Rate Limit | `backend/app/auth/hashing.py:14` | Bcrypt salted hashing, strong password policy, IP rate limiting | `test_lab009_auth.py` |
| **LAB-010** | Insecure Session Management | `backend/app/auth/session.py:18` | 256-bit cryptographic tokens, server-side TTL, `HttpOnly` cookie flags | `test_lab010_session.py` |
| **LAB-011** | Business Logic Flaw | `backend/app/api/cart.py:38` | Server-side pricing from database records, assert `quantity > 0` | `test_lab011_business_logic.py` |
| **LAB-012** | Race Condition (Double-Claim) | `backend/app/api/cart.py:146` | Atomic SQL updates (`UPDATE ... WHERE promo_claimed = FALSE`) | `test_lab012_race_condition.py` |

---

## 6. Learning Progression (Levels 1 through 8)

Follow this 8-level progression to master application security:

```
Level 1: Find Vulnerabilities
   │  Use manual code review, browser DevTools, and UI exploration to discover flaws.
   ▼
Level 2: Understand Root Causes
   │  Read the companion docs in docs/vulnerabilities/ to understand WHY the code is insecure.
   ▼
Level 3: Fix Vulnerabilities
   │  Modify the backend codebase or switch SECURE_MODE=true to enforce safe code patterns.
   ▼
Level 4: Write Regression Tests
   │  Execute the security test suite in tests/security/ to verify automated test assertions.
   ▼
Level 5: Threat-Model the Application
   │  Study docs/threat-model.md to map trust boundaries, data flows, and STRIDE threats.
   ▼
Level 6: Harden Docker / Nginx / Database
   │  Audit Dockerfiles, restrict container privileges, enable Nginx security headers, and secure PostgreSQL.
   ▼
Level 7: Add DevSecOps
   │  Inspect .github/workflows/security-ci.yml for SAST (Bandit), secret checks, and dependency audits.
   ▼
Level 8: Deploy Secure Version Locally
   │  Run the hardened stack in SECURE_MODE=true and confirm all security regression tests pass!
```

---

## 7. Documentation Index

- [Threat Model](docs/threat-model.md)
- [Security Architecture Checklist](docs/security-checklist.md)
- [Security Remediation Guide](docs/security-remediation-guide.md)
- [Vulnerability Guides](docs/vulnerabilities/)
  - [LAB-001: Broken Access Control (IDOR)](docs/vulnerabilities/LAB-001.md)
  - [LAB-002: SQL Injection](docs/vulnerabilities/LAB-002.md)
  - [LAB-003: Stored XSS](docs/vulnerabilities/LAB-003.md)
  - [LAB-004: Reflected XSS](docs/vulnerabilities/LAB-004.md)
  - [LAB-005: CSRF](docs/vulnerabilities/LAB-005.md)
  - [LAB-006: Insecure File Upload](docs/vulnerabilities/LAB-006.md)
  - [LAB-007: Path Traversal](docs/vulnerabilities/LAB-007.md)
  - [LAB-008: Server-Side Request Forgery](docs/vulnerabilities/LAB-008.md)
  - [LAB-009: Weak Authentication](docs/vulnerabilities/LAB-009.md)
  - [LAB-010: Insecure Session Management](docs/vulnerabilities/LAB-010.md)
  - [LAB-011: Business Logic Flaw](docs/vulnerabilities/LAB-011.md)
  - [LAB-012: Race Condition](docs/vulnerabilities/LAB-012.md)
