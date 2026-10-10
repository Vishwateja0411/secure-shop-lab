# SecureShop Lab — Security Remediation Guide

This guide establishes the 7-step pedagogical methodology for identifying, investigating, resolving, and testing vulnerabilities within SecureShop Lab.

---

## The 7-Step Remediation Workflow

```
+-------------------------------------------------------------+
| 1. Vulnerable Code (Locate insecure pattern in codebase)    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 2. Understand Root Cause (Analyze why the flaw exists)      |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 3. Reproduce Locally (Demonstrate the flaw using lab tools) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 4. Implement Fix (Apply secure coding remediation pattern)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 5. Run Security Test (Execute targeted pytest suite)        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 6. Verify Fix (Confirm defense blocks malicious input)      |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 7. Add Regression Test (Ensure perpetual CI/CD protection)  |
+-------------------------------------------------------------+
```

---

## Detailed Step-by-Step Breakdown

### Step 1: Locate Vulnerable Code
- Search the codebase for known anti-patterns (e.g. raw string concatenation in SQL queries, missing ownership checks, unvalidated file paths, ambient cookie authentication without CSRF tokens).
- In SecureShop Lab, all intentional training vulnerabilities are tagged with comments:
  ```python
  # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-XXX)
  ```

### Step 2: Understand the Root Cause
- Answer the fundamental questions:
  * What assumption did the developer make that was incorrect?
  * What trust boundary was violated?
  * Why does the framework or language fail to protect this by default?
- Focus on root causes (e.g. "mixing code and data in SQL queries") rather than mere symptoms.

### Step 3: Reproduce Locally in the Safe Lab
- Trigger the weakness using the browser UI, curl, or Python requests against the local Docker containers.
- Observe the insecure response (e.g. another user's order displayed, arbitrary file content returned, or duplicate promo credits awarded).
- Never run reproduction steps against third-party or production systems.

### Step 4: Implement Secure Remediation
- Replace insecure code with defense-in-depth patterns:
  * For Injection: Use parameterized queries or ORM models.
  * For Broken Access Control: Enforce object ownership checks (`current_user.id == resource.user_id`).
  * For Path Traversal: Resolve canonical paths with `os.path.realpath()` and verify base directory prefix.
  * For XSS: Implement contextual output encoding and configure Content-Security-Policy (CSP).
  * For SSRF: Enforce strict URL domain and path allowlisting; block private/loopback IP ranges.
  * For Race Conditions: Apply row-level locks (`SELECT ... FOR UPDATE`) or atomic SQL queries.

### Step 5: Run Security Tests
- Execute automated security tests with pytest:
  ```bash
  pytest tests/security/test_lab001_idor.py -v
  ```
- Compare behavior between `SECURE_MODE=false` (expected failure) and `SECURE_MODE=true` (passing assertions).

### Step 6: Verify Fix
- Re-run the reproduction request to verify that:
  1. The malicious or out-of-bounds input is safely rejected (e.g. returning 400 Bad Request or 403 Forbidden).
  2. Legitimate user actions remain fully functional without regressions.
  3. A structured security audit event is logged.

### Step 7: Add Regression Tests to CI/CD
- Ensure the automated test is committed into `tests/security/`.
- In the CI pipeline (`.github/workflows/security-ci.yml`), tests run on every pull request to guarantee future commits never reintroduce the vulnerability.
