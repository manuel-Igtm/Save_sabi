# Save Sabi API Documentation

This document describes all REST API endpoints for the Save Sabi smart savings platform.

## Base URL

- **Local Development**: `http://localhost:8000/api/v1/`
- **Production**: `https://your-domain.run.app/api/v1/`

## Authentication

All endpoints (except `/auth/register/` and `/auth/login/`) require authentication via Token.

```
Authorization: Token <your-token>
```

---

## Auth Endpoints

### Register User
**POST** `/auth/register/`

Create a new user account and primary wallet.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password_confirm": "string",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string (optional)"
}
```

**Response:** `201 Created`
```json
{
  "token": "abc123...",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  }
}
```

### Login
**POST** `/auth/login/`

Authenticate user and get token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:** `200 OK`
```json
{
  "token": "abc123...",
  "user": { ... }
}
```

### Get Profile
**GET** `/auth/profile/`

Get authenticated user's profile.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string",
  "preferred_currency": "KES",
  "created_at": "datetime"
}
```

---

## Wallet Endpoints

### List Wallets
**GET** `/wallets/`

List all user's wallets.

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `is_primary` (boolean): Filter by primary wallet

**Response:** `200 OK`
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "name": "Primary Wallet",
      "currency": "KES",
      "balance_savings": "1000.00",
      "balance_spend": "5000.00",
      "total_balance": "6000.00",
      "savings_ratio": 20,
      "spend_ratio": 80,
      "is_primary": true,
      "is_active": true,
      "created_at": "datetime"
    }
  ]
}
```

### Create Wallet
**POST** `/wallets/`

Create a new wallet.

**Request Body:**
```json
{
  "name": "string",
  "currency": "KES",
  "savings_ratio": 20
}
```

**Response:** `201 Created`

### Get Wallet
**GET** `/wallets/{id}/`

Get wallet details.

### Update Wallet
**PATCH** `/wallets/{id}/`

Update wallet settings.

**Request Body:**
```json
{
  "name": "string",
  "savings_ratio": 25
}
```

### Transfer to Savings
**POST** `/wallets/{id}/transfer_to_savings/`

Manually move funds from spend balance to savings.

**Request Body:**
```json
{
  "amount": "500.00"
}
```

**Response:** `200 OK`
```json
{
  "message": "Transferred 500.00 to savings",
  "new_savings_balance": "1500.00",
  "new_spend_balance": "4500.00"
}
```

---

## Transaction Endpoints

### List Transactions
**GET** `/transactions/`

List user's transactions with filtering.

**Query Parameters:**
- `wallet` (uuid): Filter by wallet ID
- `category` (string): Filter by category (salary, business, food, transport, etc.)
- `direction` (string): Filter by direction (in, out)
- `date_from` (date): Start date filter
- `date_to` (date): End date filter
- `ordering` (string): Order by field (-created_at, amount, etc.)

**Response:** `200 OK`
```json
{
  "count": 10,
  "results": [
    {
      "id": "uuid",
      "wallet_id": "uuid",
      "amount": "1000.00",
      "currency": "KES",
      "category": "salary",
      "direction": "in",
      "saved_portion": "200.00",
      "spend_portion": "800.00",
      "round_up_credit": "0.00",
      "notes": "Monthly salary",
      "merchant": "",
      "created_at": "datetime"
    }
  ]
}
```

### Create Transaction
**POST** `/transactions/`

Record a new transaction with automatic 80/20 split for income.

**Request Body:**
```json
{
  "wallet_id": "uuid (optional, uses primary wallet)",
  "amount": "1000.00",
  "category": "salary",
  "direction": "in",
  "round_up": false,
  "metadata": {
    "notes": "Monthly salary",
    "merchant": "Employer Inc."
  }
}
```

**Response:** `201 Created`

**Categories:**
- Income: `salary`, `business`, `gift`, `other`
- Expense: `food`, `transport`, `utilities`, `entertainment`, `shopping`, `health`, `education`, `rent`, `other`

### Get Transaction
**GET** `/transactions/{id}/`

Get transaction details.

---

## Summary Endpoints

### Get Summary
**GET** `/summaries/`

Get wallet summary and analytics.

**Query Parameters:**
- `wallet_id` (uuid): Specific wallet (optional, uses primary)
- `range` (string): Period - `7d`, `30d`, `90d`, `365d`, `custom`
- `date_from` (date): Start date (required for custom range)
- `date_to` (date): End date (required for custom range)

**Response:** `200 OK`
```json
{
  "period": "30d",
  "date_from": "2025-01-01",
  "date_to": "2025-01-31",
  "total_in": "50000.00",
  "total_out": "35000.00",
  "total_saved": "10000.00",
  "transaction_count": 45,
  "savings_rate": "20.00",
  "categories": [
    {
      "category": "food",
      "total": "15000.00",
      "count": 20,
      "percentage": "42.86"
    }
  ],
  "goal_progress": [
    {
      "id": "uuid",
      "name": "Emergency Fund",
      "target_amount": "100000.00",
      "saved_amount": "25000.00",
      "progress_pct": "25.00"
    }
  ],
  "current_streak": 15,
  "longest_streak": 30
}
```

---

## Goal Endpoints

### List Goals
**GET** `/goals/`

List user's savings goals.

**Query Parameters:**
- `wallet` (uuid): Filter by wallet
- `status` (string): Filter by status (active, paused, completed, cancelled)

**Response:** `200 OK`
```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "wallet_id": "uuid",
      "name": "Emergency Fund",
      "description": "6 months expenses",
      "target_amount": "100000.00",
      "target_date": "2025-12-31",
      "saved_amount": "25000.00",
      "status": "active",
      "priority": 1,
      "allocation_percentage": 50,
      "progress_percentage": "25.00",
      "remaining_amount": "75000.00",
      "is_completed": false,
      "created_at": "datetime"
    }
  ]
}
```

### Create Goal
**POST** `/goals/`

Create a new savings goal.

**Request Body:**
```json
{
  "wallet_id": "uuid (optional)",
  "name": "Emergency Fund",
  "description": "6 months of living expenses",
  "target_amount": "100000.00",
  "target_date": "2025-12-31",
  "priority": 1,
  "allocation_percentage": 50
}
```

### Update Goal
**PATCH** `/goals/{id}/`

Update goal details.

### Contribute to Goal
**POST** `/goals/{id}/contribute/`

Contribute to a goal from savings balance.

**Request Body:**
```json
{
  "amount": "5000.00"
}
```

**Response:** `200 OK`
```json
{
  "goal_id": "uuid",
  "amount_contributed": "5000.00",
  "new_saved_amount": "30000.00",
  "progress_pct": "30.00",
  "remaining_amount": "70000.00",
  "is_completed": false
}
```

### Withdraw from Goal
**POST** `/goals/{id}/withdraw/`

Withdraw from a goal back to savings balance.

**Request Body:**
```json
{
  "amount": "1000.00"
}
```

---

## Budget Rule Endpoints

### List Rules
**GET** `/rules/`

List user's budget rules.

**Response:** `200 OK`
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "wallet_id": "uuid",
      "rule_type": "category_limit",
      "category": "food",
      "threshold_amount": "10000.00",
      "period": "monthly",
      "custom_message": "",
      "is_active": true,
      "created_at": "datetime"
    }
  ]
}
```

### Create Rule
**POST** `/rules/`

Create a new budget rule.

**Request Body:**
```json
{
  "wallet_id": "uuid (optional)",
  "rule_type": "category_limit",
  "category": "food",
  "threshold_amount": "10000.00",
  "period": "monthly",
  "custom_message": "Watch your food spending!"
}
```

**Rule Types:**
- `category_limit`: Limit spending in a category
- `daily_limit`: Daily total spending limit
- `savings_minimum`: Minimum savings balance alert

**Periods:**
- `daily`, `weekly`, `monthly`

### Update Rule
**PATCH** `/rules/{id}/`

Update rule settings.

### Delete Rule
**DELETE** `/rules/{id}/`

Delete a budget rule.

---

## Nudge Endpoints

### List Nudges
**GET** `/nudges/`

List user's nudges/alerts.

**Query Parameters:**
- `is_read` (boolean): Filter by read status
- `alert_type` (string): Filter by type (info, warning, alert, celebration)

**Response:** `200 OK`
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "wallet_id": "uuid",
      "rule_id": "uuid",
      "alert_type": "warning",
      "title": "Food budget exceeded",
      "message": "You've spent 12,000 KES on food this month (limit: 10,000 KES)",
      "sent_via": "in_app",
      "is_read": false,
      "read_at": null,
      "created_at": "datetime"
    }
  ]
}
```

### Acknowledge Nudges
**POST** `/nudges/acknowledge/`

Mark nudges as read.

**Request Body:**
```json
{
  "nudge_ids": ["uuid1", "uuid2"]
}
```

**Response:** `200 OK`
```json
{
  "acknowledged_count": 2,
  "acknowledged": ["uuid1", "uuid2"]
}
```

---

## Health Check

### Health Check
**GET** `/healthz`

Check API health status.

**Response:** `200 OK`
```json
{
  "status": "ok",
  "database": "healthy",
  "timestamp": "2025-01-20T12:00:00Z"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": { ... }
}
```

**Common Error Codes:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Business rule violation
- `500 Internal Server Error`: Server error

---

## Rate Limiting

- **Anonymous**: 100 requests/day
- **Authenticated**: 1000 requests/day

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1705766400
```
