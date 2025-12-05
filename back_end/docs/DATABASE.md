# Save Sabi - Database Schema Documentation

This document describes the database schema and relationships for Save Sabi.

## Entity Relationship Diagram

```
┌──────────────────┐
│       User       │
│──────────────────│
│ id (PK)          │
│ username         │
│ email            │
│ password         │
│ phone_number     │
│ preferred_currency│
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │
         │ 1:N
         ▼
┌──────────────────┐      1:N      ┌──────────────────┐
│      Wallet      │──────────────▶│   Transaction    │
│──────────────────│               │──────────────────│
│ id (PK)          │               │ id (PK)          │
│ owner_id (FK)    │               │ wallet_id (FK)   │
│ name             │               │ amount           │
│ currency         │               │ currency         │
│ balance_savings  │               │ category         │
│ balance_spend    │               │ direction        │
│ savings_ratio    │               │ saved_portion    │
│ is_primary       │               │ spend_portion    │
│ is_active        │               │ round_up_amount  │
│ created_at       │               │ metadata (JSON)  │
│ updated_at       │               │ created_at       │
└────────┬─────────┘               └──────────────────┘
         │
         │ 1:N
         ├─────────────────────────────┐
         │                             │
         ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│       Goal       │         │   BudgetRule     │
│──────────────────│         │──────────────────│
│ id (PK)          │         │ id (PK)          │
│ wallet_id (FK)   │         │ wallet_id (FK)   │
│ name             │         │ rule_type        │
│ description      │         │ category         │
│ target_amount    │         │ threshold_amount │
│ target_date      │         │ period           │
│ saved_amount     │         │ custom_message   │
│ status           │         │ is_active        │
│ priority         │         │ created_at       │
│ allocation_%     │         │ updated_at       │
│ created_at       │         └────────┬─────────┘
│ updated_at       │                  │
└──────────────────┘                  │ 1:N
                                      │
         ┌────────────────────────────┘
         │
         ▼
┌──────────────────┐         ┌──────────────────┐
│      Nudge       │         │  SavingsStreak   │
│──────────────────│         │──────────────────│
│ id (PK)          │         │ id (PK)          │
│ wallet_id (FK)   │         │ wallet_id (FK)   │
│ rule_id (FK)     │         │ current_streak   │
│ alert_type       │         │ longest_streak   │
│ title            │         │ last_savings_date│
│ message          │         │ created_at       │
│ sent_via         │         │ updated_at       │
│ is_read          │         └──────────────────┘
│ read_at          │
│ metadata (JSON)  │
│ created_at       │
└──────────────────┘
```

## Tables

### User
Extended Django AbstractUser for authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| username | VARCHAR(150) | UNIQUE, NOT NULL | Username for login |
| email | VARCHAR(254) | UNIQUE, NOT NULL | Email address |
| password | VARCHAR(128) | NOT NULL | Hashed password |
| first_name | VARCHAR(150) | | First name |
| last_name | VARCHAR(150) | | Last name |
| phone_number | VARCHAR(20) | | Phone for notifications |
| preferred_currency | VARCHAR(3) | DEFAULT 'KES' | Default currency |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| date_joined | DATETIME | AUTO | Registration date |
| last_login | DATETIME | | Last login timestamp |

**Indexes:**
- `user_username_idx` on `username`
- `user_email_idx` on `email`

---

### Wallet
User's savings wallet with 80/20 split configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| owner_id | UUID | FK → User | Wallet owner |
| name | VARCHAR(100) | NOT NULL | Wallet name |
| currency | VARCHAR(3) | DEFAULT 'KES' | Wallet currency |
| balance_savings | DECIMAL(14,2) | DEFAULT 0.00 | Savings balance |
| balance_spend | DECIMAL(14,2) | DEFAULT 0.00 | Spendable balance |
| savings_ratio | INTEGER | DEFAULT 20 | Savings percentage (1-99) |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary wallet flag |
| is_active | BOOLEAN | DEFAULT TRUE | Soft delete flag |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Last update |

**Constraints:**
- `savings_ratio BETWEEN 1 AND 99`
- Only one `is_primary=TRUE` per user

**Indexes:**
- `wallet_owner_idx` on `owner_id`
- `wallet_active_idx` on `is_active`

**Computed:**
- `spend_ratio = 100 - savings_ratio`
- `total_balance = balance_savings + balance_spend`

---

### Transaction
Financial transaction record with automatic 80/20 split.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| wallet_id | UUID | FK → Wallet | Associated wallet |
| amount | DECIMAL(14,2) | NOT NULL | Transaction amount |
| currency | VARCHAR(3) | NOT NULL | Transaction currency |
| category | VARCHAR(20) | NOT NULL | Transaction category |
| direction | VARCHAR(3) | NOT NULL | 'in' or 'out' |
| saved_portion | DECIMAL(14,2) | DEFAULT 0.00 | Amount to savings |
| spend_portion | DECIMAL(14,2) | DEFAULT 0.00 | Amount to spend |
| round_up_amount | DECIMAL(14,2) | DEFAULT 0.00 | Round-up savings |
| metadata | JSONB | DEFAULT {} | Extra data (notes, merchant) |
| created_at | DATETIME | AUTO | Transaction time |

**Category Enum:**
```
salary, business, gift, food, transport, utilities,
entertainment, shopping, health, education, rent, other
```

**Direction Enum:**
```
in, out
```

**Indexes:**
- `txn_wallet_idx` on `wallet_id`
- `txn_created_idx` on `created_at DESC`
- `txn_category_idx` on `category`
- `txn_direction_idx` on `direction`

**Business Logic:**
- Income (`direction=in`): Split by `savings_ratio`
- Expense (`direction=out`): Deduct from `balance_spend`
- Round-up: Optional extra savings from expenses

---

### Goal
Savings goal with progress tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| wallet_id | UUID | FK → Wallet | Associated wallet |
| name | VARCHAR(100) | NOT NULL | Goal name |
| description | TEXT | | Goal description |
| target_amount | DECIMAL(14,2) | NOT NULL | Target to save |
| target_date | DATE | | Target completion date |
| saved_amount | DECIMAL(14,2) | DEFAULT 0.00 | Current savings |
| status | VARCHAR(20) | DEFAULT 'active' | Goal status |
| priority | INTEGER | DEFAULT 1 | Priority order |
| allocation_percentage | INTEGER | DEFAULT 0 | Auto-allocation % |
| created_at | DATETIME | AUTO | Creation time |
| updated_at | DATETIME | AUTO | Last update |

**Status Enum:**
```
active, paused, completed, cancelled
```

**Indexes:**
- `goal_wallet_idx` on `wallet_id`
- `goal_status_idx` on `status`

**Computed:**
- `progress_percentage = (saved_amount / target_amount) * 100`
- `remaining_amount = target_amount - saved_amount`
- `is_completed = saved_amount >= target_amount`

---

### BudgetRule
Budget rules for nudge triggers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| wallet_id | UUID | FK → Wallet | Associated wallet |
| rule_type | VARCHAR(20) | NOT NULL | Rule type |
| category | VARCHAR(20) | NULLABLE | Category (for limits) |
| threshold_amount | DECIMAL(14,2) | NOT NULL | Trigger threshold |
| period | VARCHAR(10) | NOT NULL | Evaluation period |
| custom_message | TEXT | | Custom alert message |
| is_active | BOOLEAN | DEFAULT TRUE | Rule active status |
| created_at | DATETIME | AUTO | Creation time |
| updated_at | DATETIME | AUTO | Last update |

**Rule Type Enum:**
```
category_limit   - Limit spending in category
daily_limit      - Daily total spending limit
savings_minimum  - Minimum savings balance
```

**Period Enum:**
```
daily, weekly, monthly
```

**Indexes:**
- `rule_wallet_idx` on `wallet_id`
- `rule_active_idx` on `is_active`

---

### Nudge
Alert/notification triggered by budget rules.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| wallet_id | UUID | FK → Wallet | Associated wallet |
| rule_id | UUID | FK → BudgetRule | Triggering rule |
| alert_type | VARCHAR(20) | NOT NULL | Alert severity |
| title | VARCHAR(200) | NOT NULL | Alert title |
| message | TEXT | NOT NULL | Alert message |
| sent_via | VARCHAR(20) | DEFAULT 'in_app' | Delivery method |
| is_read | BOOLEAN | DEFAULT FALSE | Read status |
| read_at | DATETIME | NULLABLE | When read |
| metadata | JSONB | DEFAULT {} | Extra data |
| created_at | DATETIME | AUTO | Creation time |

**Alert Type Enum:**
```
info, warning, alert, celebration
```

**Delivery Method Enum:**
```
in_app, push, sms, email
```

**Indexes:**
- `nudge_wallet_idx` on `wallet_id`
- `nudge_unread_idx` on `is_read` WHERE `is_read=FALSE`
- `nudge_created_idx` on `created_at DESC`

---

### SavingsStreak
Track consecutive savings days.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| wallet_id | UUID | FK → Wallet, UNIQUE | Associated wallet |
| current_streak | INTEGER | DEFAULT 0 | Current streak days |
| longest_streak | INTEGER | DEFAULT 0 | Best streak ever |
| last_savings_date | DATE | NULLABLE | Last saving date |
| created_at | DATETIME | AUTO | Creation time |
| updated_at | DATETIME | AUTO | Last update |

**Business Logic:**
- Increment `current_streak` on daily savings
- Reset to 0 if a day is missed
- Update `longest_streak` if current exceeds it

---

## Migrations

### Generate Migrations
```bash
python manage.py makemigrations core
```

### Apply Migrations
```bash
python manage.py migrate
```

### Show SQL
```bash
python manage.py sqlmigrate core 0001
```

### Reset Database (Development Only)
```bash
python manage.py flush
python manage.py migrate
```

---

## Performance Considerations

### Indexing Strategy
1. **Primary Keys**: UUID indexed automatically
2. **Foreign Keys**: Indexed for JOIN performance
3. **Query Filters**: Indexed columns used in WHERE clauses
4. **Sorting**: Index on `created_at DESC` for recent-first queries

### Query Optimization
1. Use `select_related()` for FK joins
2. Use `prefetch_related()` for reverse FK
3. Paginate large result sets
4. Use `only()` for partial field selection

### Example Optimized Query
```python
# Bad: N+1 queries
transactions = Transaction.objects.filter(wallet__owner=user)
for txn in transactions:
    print(txn.wallet.name)  # Extra query per transaction

# Good: Single query with JOIN
transactions = Transaction.objects.filter(
    wallet__owner=user
).select_related('wallet')
```

---

## Future: Firestore Migration

The repository pattern allows swapping PostgreSQL for Firestore:

```python
# Current: PostgreSQL
class PostgresWalletRepository(WalletRepositoryBase):
    def get_by_id(self, wallet_id):
        return Wallet.objects.get(id=wallet_id)

# Future: Firestore
class FirestoreWalletRepository(WalletRepositoryBase):
    def get_by_id(self, wallet_id):
        doc = db.collection('wallets').document(wallet_id).get()
        return self._to_wallet(doc)
```

Firestore collection structure would mirror the relational schema with denormalization where needed for query performance.
