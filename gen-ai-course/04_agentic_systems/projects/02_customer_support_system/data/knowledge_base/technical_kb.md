# Technical Knowledge Base

## Getting Started — Setup Guide

### System Requirements
- **Operating System:** Windows 10+, macOS 11+, Ubuntu 20.04+
- **Node.js:** 18.x or later (for web SDK)
- **Python:** 3.9 or later (for Python SDK)
- **Memory:** Minimum 4 GB RAM recommended for local development
- **Network:** HTTPS outbound on port 443 required

### Installation — Python SDK
```bash
pip install support-platform-sdk
```

Configure your API key:
```python
import support_platform as sp
sp.configure(api_key="YOUR_API_KEY")
```

Or set the environment variable:
```bash
export SUPPORT_PLATFORM_API_KEY="YOUR_API_KEY"
```

### Installation — JavaScript / Node.js SDK
```bash
npm install @support-platform/sdk
```

```javascript
const SupportPlatform = require('@support-platform/sdk');
const client = new SupportPlatform({ apiKey: process.env.SUPPORT_PLATFORM_API_KEY });
```

### First API Call — Health Check
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.support-platform.com/v1/health
```
Expected response:
```json
{"status": "ok", "version": "3.2.1", "region": "us-east-1"}
```

---

## API Documentation

### Base URL
```
https://api.support-platform.com/v1
```

### Authentication
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

API keys can be created and revoked at **Settings → Developer → API Keys**. Always use environment variables — never hardcode API keys in source code.

### Rate Limits
| Plan         | Requests/minute | Requests/day |
|--------------|----------------|--------------|
| Starter      | 60             | 5,000        |
| Professional | 300            | 50,000       |
| Enterprise   | Custom         | Custom       |

Rate limit headers are returned with every response:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1704067200
```

When the rate limit is exceeded, the API returns **HTTP 429 Too Many Requests**.

### Pagination
List endpoints are paginated. Use `page` and `per_page` query parameters:
```
GET /v1/tickets?page=2&per_page=50
```
Response includes:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total": 342,
    "total_pages": 7
  }
}
```

### Core Endpoints

#### Tickets
- `POST /v1/tickets` — Create a new support ticket
- `GET /v1/tickets/{id}` — Get ticket details
- `PATCH /v1/tickets/{id}` — Update ticket status/notes
- `DELETE /v1/tickets/{id}` — Archive a ticket

#### Users
- `POST /v1/users` — Create user
- `GET /v1/users/{id}` — Get user profile
- `PATCH /v1/users/{id}` — Update user
- `DELETE /v1/users/{id}` — Deactivate user

#### Sessions
- `POST /v1/sessions` — Start a new chat session
- `GET /v1/sessions/{id}` — Get session with message history
- `DELETE /v1/sessions/{id}` — End session

---

## Common Error Codes and Fixes

### HTTP 400 — Bad Request
**Cause:** The request body is malformed or missing required fields.
**Fix:**
1. Check the request Content-Type header is `application/json`.
2. Validate your JSON payload against the API schema.
3. Ensure all required fields are present. Required fields are documented with `*` in the API reference.

Example error response:
```json
{"error": "validation_error", "message": "Field 'user_id' is required", "field": "user_id"}
```

### HTTP 401 — Unauthorized
**Cause:** Missing, expired, or invalid API key.
**Fix:**
1. Verify the Authorization header format: `Bearer YOUR_API_KEY` (note the space after "Bearer").
2. Check that your API key is active in **Settings → Developer → API Keys**.
3. Regenerate the key if it may have been compromised.
4. Ensure you are not using a test-mode key against the production endpoint (or vice versa).

### HTTP 403 — Forbidden
**Cause:** Valid API key but insufficient permissions.
**Fix:**
1. Check the key's permission scopes in **Settings → Developer → API Keys → Edit**.
2. Required scopes are listed in each endpoint's documentation.
3. If you need elevated permissions, contact your account administrator.

### HTTP 404 — Not Found
**Cause:** The requested resource does not exist, or the resource ID belongs to a different organization.
**Fix:**
1. Double-check the resource ID in the URL.
2. Ensure you are authenticated with the correct API key for the correct organization.
3. Check if the resource was deleted or archived.

### HTTP 422 — Unprocessable Entity
**Cause:** The request body is valid JSON but contains semantic errors.
**Fix:**
1. Review the error message in the response body — it specifies which field is invalid and why.
2. Common causes: invalid enum value, date format mismatch, string exceeds max length.

### HTTP 429 — Too Many Requests
**Cause:** Rate limit exceeded.
**Fix:**
1. Check `X-RateLimit-Reset` header for when the limit resets (Unix timestamp).
2. Implement exponential backoff in your client.
3. Cache responses where possible to reduce API call frequency.
4. Upgrade to a higher plan for increased rate limits.

### HTTP 500 — Internal Server Error
**Cause:** Unexpected error on our servers.
**Fix:**
1. Check our status page at status.support-platform.com.
2. Retry the request after 30 seconds. Most 500 errors are transient.
3. If the error persists for more than 5 minutes, contact technical support with the `X-Request-ID` header value from the failed response.

### HTTP 503 — Service Unavailable
**Cause:** Planned maintenance or unexpected outage.
**Fix:**
1. Check status.support-platform.com for maintenance windows.
2. Subscribe to status updates at status.support-platform.com/subscribe.
3. Implement retry logic with jitter in your integration.

---

## Integration Guides

### Webhooks
Webhooks allow you to receive real-time notifications when events occur in your account.

**Setting up a webhook:**
1. Go to **Settings → Developer → Webhooks**.
2. Click **Add Endpoint**.
3. Enter your HTTPS endpoint URL (must respond with HTTP 200 within 5 seconds).
4. Select the events you want to subscribe to.
5. Save and note your **Webhook Secret** (used for signature verification).

**Verifying webhook signatures:**
```python
import hmac, hashlib

def verify_webhook(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)
```

**Retry policy:** Failed deliveries (non-200 responses or timeouts) are retried up to 5 times with exponential backoff: 1 min, 5 min, 30 min, 2 hours, 8 hours.

**Event types:**
- `ticket.created` — New ticket submitted
- `ticket.resolved` — Ticket marked resolved
- `ticket.escalated` — Ticket escalated to human
- `session.started` — New chat session begun
- `user.created` — New user account created

### OAuth 2.0 Integration
Use OAuth 2.0 to allow your users to authenticate with our platform on behalf of your application.

**Authorization URL:**
```
https://auth.support-platform.com/oauth/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://yourapp.com/callback&
  scope=read:tickets+write:tickets&
  response_type=code&
  state=RANDOM_STATE_VALUE
```

**Exchanging the authorization code for tokens:**
```bash
curl -X POST https://auth.support-platform.com/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://yourapp.com/callback"
```

**Token response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "dGhp..."
}
```

Access tokens expire after 1 hour. Use the refresh token to obtain a new access token without requiring the user to re-authenticate.

---

## Troubleshooting Guide

### Issue: SDK returns "Connection refused" or "Network Error"
**Steps:**
1. Confirm your network allows outbound HTTPS on port 443.
2. Test connectivity: `curl -v https://api.support-platform.com/v1/health`
3. Check for corporate proxies or firewalls. If behind a proxy, configure your HTTP client accordingly.
4. Verify DNS resolution: `nslookup api.support-platform.com`

### Issue: Webhooks are not being received
**Steps:**
1. Ensure your endpoint returns HTTP 200 within 5 seconds for every webhook.
2. Check webhook delivery logs in **Settings → Developer → Webhooks → View Logs**.
3. Verify your endpoint URL is publicly accessible (not localhost or an internal IP).
4. If using HTTPS, ensure your SSL certificate is valid and not self-signed.
5. Temporarily set up a tool like webhook.site to confirm event delivery, then debug your endpoint.

### Issue: OAuth tokens expire unexpectedly
**Steps:**
1. Access tokens are valid for 3600 seconds (1 hour). Implement token refresh logic.
2. Store the refresh token securely (never in localStorage or session cookies).
3. If the refresh token is also expiring, check your OAuth app's `refresh_token_expiry` setting.

### Issue: API responses are slow (> 2 seconds)
**Steps:**
1. Check the `X-Response-Time` header — values over 500ms indicate server-side processing time.
2. Use the `fields` query parameter to request only the fields you need.
3. Enable response compression: `Accept-Encoding: gzip`.
4. Check status.support-platform.com for regional degradation.
5. If on the Starter plan, consider upgrading — higher plans have priority request queuing.

### Issue: Python SDK raises `ImportError`
**Steps:**
1. Ensure you are using Python 3.9+: `python --version`
2. Install/upgrade: `pip install --upgrade support-platform-sdk`
3. Check for conflicting packages: `pip show support-platform-sdk`
4. Use a virtual environment to isolate dependencies.

---

## SDK Changelog and Version Compatibility

| SDK Version | API Version | Breaking Changes                        |
|-------------|-------------|-----------------------------------------|
| 3.x         | v1          | None (current)                          |
| 2.x         | v1          | `client.send()` renamed to `client.create_ticket()` |
| 1.x         | v0 (EOL)    | v0 API deprecated as of Jan 2024        |

**Migration from SDK 2.x to 3.x:**
- Replace `client.send(message)` with `client.create_ticket(message=message)`
- The `session_id` parameter is now required for chat-mode calls
- Response objects now include `confidence_score` and `assigned_agent` fields

---

## Technical Support Contact
- **Email:** tech@support-platform.com
- **Developer Slack:** support-platform.slack.com/channels/developer-support
- **Status Page:** status.support-platform.com
- **API Documentation:** docs.support-platform.com
- **Hours:** 24/7 for Enterprise; Monday–Friday 9 AM–6 PM EST for Starter/Professional
