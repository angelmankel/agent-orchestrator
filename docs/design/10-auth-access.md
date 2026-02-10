# Authentication & Access Control

> **Status**: Draft
> **Last Updated**: 2026-02-05
> **Owner**: -
> **Depends On**: [01-architecture](01-architecture.md), [07-api-design](07-api-design.md)

---

## Overview

Authentication and authorization system for the Agent Orchestrator. Supports single-user local mode and multi-user hosted mode with role-based access control.

---

## Goals

- [ ] Secure API access with JWT tokens
- [ ] Support local mode (no auth) and hosted mode (full auth)
- [ ] Role-based access control for team scenarios
- [ ] Audit logging for sensitive operations
- [ ] Simple setup for personal use

---

## Non-Goals

- OAuth/social login (defer to v2)
- Fine-grained per-resource permissions
- SSO/SAML integration

---

## Design

### Authentication Modes

| Mode | Use Case | Auth Required |
|------|----------|---------------|
| Local | Personal use on localhost | Optional (configurable) |
| Hosted | Server deployment | Required |

### Local Mode

```yaml
# config.yaml
auth:
  mode: local
  require_auth: false  # Set to true to enable auth locally
```

When `require_auth: false`:
- All endpoints accessible without token
- Single implicit user
- Good for personal, single-machine use

### Hosted Mode

```yaml
# config.yaml
auth:
  mode: hosted
  require_auth: true
  jwt_secret: ${JWT_SECRET}  # Required
  token_expiry_hours: 24
  session_expiry_days: 30
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                         │
└─────────────────────────────────────────────────────────────────┘

    User                    API                     Database
      │                      │                          │
      │  POST /auth/login    │                          │
      │  {username, password}│                          │
      │─────────────────────>│                          │
      │                      │  Verify credentials      │
      │                      │─────────────────────────>│
      │                      │                          │
      │                      │  User record             │
      │                      │<─────────────────────────│
      │                      │                          │
      │                      │  Generate JWT            │
      │                      │  Create session          │
      │                      │─────────────────────────>│
      │                      │                          │
      │  {token, expires_at} │                          │
      │<─────────────────────│                          │
      │                      │                          │
      │  GET /api/projects   │                          │
      │  Authorization: Bearer <token>                  │
      │─────────────────────>│                          │
      │                      │  Validate JWT            │
      │                      │  Check permissions       │
      │                      │                          │
      │  {projects: [...]}   │                          │
      │<─────────────────────│                          │
```

### JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid",
    "username": "donny",
    "role": "admin",
    "iat": 1738747800,
    "exp": 1738834200
  }
}
```

### Password Security

```python
# Password hashing with bcrypt
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())
```

### Roles & Permissions

#### Roles

| Role | Description |
|------|-------------|
| `admin` | Full access to all features |
| `developer` | Can submit ideas, view queue, cannot manage agents |
| `viewer` | Read-only access |

#### Permission Matrix

| Action | Admin | Developer | Viewer |
|--------|-------|-----------|--------|
| View dashboard | ✅ | ✅ | ✅ |
| Submit ideas | ✅ | ✅ | ❌ |
| Answer questions | ✅ | ✅ | ❌ |
| Approve ideas | ✅ | ❌ | ❌ |
| View dev queue | ✅ | ✅ | ✅ |
| Approve tickets | ✅ | ❌ | ❌ |
| Manage agents | ✅ | ❌ | ❌ |
| View planning docs | ✅ | ✅ | ✅ |
| Edit planning docs | ✅ | ✅ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| View usage/costs | ✅ | ❌ | ❌ |
| Change settings | ✅ | ❌ | ❌ |

### Authorization Middleware

```python
# Pseudocode
def require_auth(required_role: str = None):
    def middleware(request):
        # 1. Extract token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            raise UnauthorizedError("No token provided")

        # 2. Validate JWT
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token expired")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Invalid token")

        # 3. Check role if required
        if required_role:
            user_role = payload.get("role")
            if not has_permission(user_role, required_role):
                raise ForbiddenError("Insufficient permissions")

        # 4. Attach user to request
        request.user = payload
        return request

    return middleware
```

### API Key Authentication (Optional)

For programmatic access without login flow:

```yaml
# config.yaml
auth:
  api_keys:
    enabled: true
    keys:
      - name: ci-pipeline
        key: ${CI_API_KEY}
        role: developer
        expires: null  # Never expires
      - name: monitoring
        key: ${MONITOR_API_KEY}
        role: viewer
        expires: "2026-12-31"
```

Usage:
```
Authorization: ApiKey <key>
```

### Session Management

```sql
CREATE TABLE sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    token           TEXT NOT NULL UNIQUE,
    ip_address      TEXT,
    user_agent      TEXT,
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Session cleanup:
```sql
-- Run periodically
DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP;
```

### Audit Logging

Log sensitive operations for security review:

```sql
CREATE TABLE audit_log (
    id              TEXT PRIMARY KEY,
    user_id         TEXT REFERENCES users(id),
    action          TEXT NOT NULL,
    resource_type   TEXT,
    resource_id     TEXT,
    details         TEXT,  -- JSON
    ip_address      TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at);
```

Logged actions:
- `auth.login`, `auth.logout`, `auth.failed_login`
- `idea.approve`, `idea.reject`
- `ticket.approve`, `ticket.reject`
- `agent.create`, `agent.update`, `agent.delete`
- `user.create`, `user.update`, `user.delete`
- `settings.update`

### Security Headers

```python
# Response headers for all API responses
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}
```

### Rate Limiting

```python
# Per-user rate limits
rate_limits = {
    "default": "60/minute",
    "auth": "10/minute",
    "ideas.create": "30/minute",
    "agents.run": "20/minute",
}
```

---

## User Management UI

### Login Page
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                      Agent Orchestrator                         │
│                                                                 │
│              ┌─────────────────────────────────┐                │
│              │ Username                        │                │
│              │ [_____________________________] │                │
│              │                                 │                │
│              │ Password                        │                │
│              │ [_____________________________] │                │
│              │                                 │                │
│              │ [        Sign In        ]       │                │
│              │                                 │                │
│              │ □ Remember me                   │                │
│              └─────────────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### User Management (Admin)
```
┌─────────────────────────────────────────────────────────────────┐
│ User Management                                      [+ New User]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Username        Email                  Role      Last Login     │
│ ─────────────────────────────────────────────────────────────── │
│ donny           donny@example.com      Admin     2h ago    [Edit]│
│ alice           alice@example.com      Developer 1d ago    [Edit]│
│ bob             bob@example.com        Viewer    3d ago    [Edit]│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## First-Time Setup

### Local Mode
```bash
# No setup required, just run
agent-orchestrator serve
```

### Hosted Mode
```bash
# 1. Set environment variables
export JWT_SECRET=$(openssl rand -hex 32)
export ANTHROPIC_API_KEY=sk-ant-...

# 2. Initialize database with admin user
agent-orchestrator init --admin-user donny --admin-password <password>

# 3. Start server
agent-orchestrator serve --mode hosted
```

---

## Open Questions

| Question | Context | Decision |
|----------|---------|----------|
| Password reset flow? | Email-based recovery | TBD - defer, manual for now |
| 2FA support? | Enhanced security | TBD - defer to v2 |
| Session invalidation? | Logout from all devices | TBD - add to v1 |

---

## Dependencies

- **Depends on**: 01-architecture, 07-api-design
- **Depended by**: 08-web-ui

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-05 | Initial draft | - |
