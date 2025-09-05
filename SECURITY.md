# Security Policy 
Updated: 2025‑09‑05
(Developer / Backend Engineer / DevOps) Technical Contact: wifiknight45@proton.me 
Business inquiries Contact: andrews.crystal@gmail.com re: Pyschic-Tribble

1. Purpose
This policy defines the security requirements, controls, and operational practices for the psychic‑tribble backend application. It ensures the confidentiality, integrity, and availability of the system, its APIs, and user data, while supporting secure development and deployment.

2. Scope
Applies to:
All psychic‑tribble code, infrastructure, and environments (development, staging, production).
All data processed by the application, including authentication tokens, user credentials, and calendar/event data.
All supporting services (databases, Redis, CI/CD pipelines, hosting platforms).

3. Roles & Responsibilities
Sole Developer / DevOps Engineer:
Implement and maintain all security controls.
Monitor logs, alerts, and rate‑limit metrics.
Apply patches and dependency updates.
Respond to incidents and security reports.

Business Contact:
Handle legal, contractual, and customer‑facing communications.

4. Access Control

Principle of Least Privilege:
Development and production credentials are separate.
No shared accounts; all access is tied to the sole developer.

Authentication:
JWT access tokens expire within 30 minutes; refresh tokens expire within 14 days.
Tokens are signed with a strong, rotated SECRET_KEY stored in .env or a secrets manager.

Authorization:
Role‑based access enforced in API routes.
Sensitive endpoints require explicit Depends(get_current_user) checks.

5. Data Protection
Encryption:
TLS 1.2+ enforced for all external traffic.
Passwords hashed with bcrypt (passlib context) before storage.
JWTs signed with HS256 and a minimum 256‑bit key.

Secrets Management:
No secrets committed to Git.
.env files ignored via .gitignore and stored securely.

Data Minimization:
Only store data required for scheduling and authentication.
Delete stale or unused data regularly.

6. Secure Development Practices
Code Quality:
All commits linted and formatted via ruff and pre‑commit hooks.
Unit and integration tests run via pytest with coverage reports.

Dependency Management:

Dependencies pinned in requirements.txt / pyproject.toml.
Monthly vulnerability scans (pip-audit or similar).

JWT Hardening:
Include aud and iss claims to prevent token reuse across contexts.
Validate exp, nbf, and iat claims on every decode.

Rate Limiting:
Default: 100 requests/minute per IP via slowapi + Redis.
Stricter limits on authentication endpoints.

7. Infrastructure & Deployment
Environment Separation:

Development, staging, and production use separate databases, Redis instances, and .env files.

CI/CD Security:
Branch protection rules enforced (main and release/*).
Required PR reviews, status checks, and signed commits.

Hosting:
Only necessary ports exposed.

Uvicorn/Gunicorn run behind a reverse proxy (e.g., Nginx) in production.

8. Monitoring & Logging
Application Logs:
Log authentication failures, rate‑limit triggers, and DB errors.
Avoid logging sensitive data (passwords, tokens).

Alerts:
Email alerts to wifiknight45@proton.me for critical errors or suspected breaches.

9. Incident Response
Detection:
Monitor logs and rate‑limit events for anomalies.

Containment:
Revoke compromised JWTs by rotating SECRET_KEY.
Block offending IPs at the firewall or reverse proxy.

Recovery:
Restore from backups if data integrity is compromised.

Notification:
Technical issues → wifiknight45@proton.me

Business/customer issues → andrews.crystal@gmail.com

10. Compliance & Review
Policy Review:
Review and update this policy quarterly or after major changes.

Audit:
Run security scans before each production deployment.
