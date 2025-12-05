# Save Sabi Architecture

## Purpose
Backend for a smart savings platform implementing the 20/80 Hara Hachib rule with kaizen nudges and goal tracking.

## High-level components
- API: Django REST Framework (stateless)
- Domain services: 20/80 split, round-ups, goal progress, nudges
- Data: Postgres by default; Firestore supported via repository layer; BigQuery optional for analytics
- Background work: Celery + Redis (or Cloud Tasks) for alerts/digests
- Observability: health endpoint, structured logs, optional Sentry

## Module boundaries
- `core.models`: User (or extension), Wallet, Transaction, Goal, BudgetRule/Nudge
- `core.serializers`: Request/response DTOs
- `core.views`: DRF viewsets/APIViews for transactions, summaries, goals, nudges
- `core.services`: Domain logic (split_20_80, apply_round_up, compute_summary, generate_nudges)
- `core.tasks`: Background jobs (daily summaries, push alerts)
- `core.repositories` (optional): Abstract DB calls so Postgres/Firestore can be swapped

## Data model (minimum viable)
- Wallet: id, owner, currency, balance_savings, balance_spend, created_at
- Transaction: id, wallet_id, amount, currency, category, direction (in/out), saved_portion, spend_portion, metadata, created_at
- Goal: id, wallet_id, name, target_amount, target_date, saved_amount, status
- BudgetRule/Nudge: id, wallet_id, rule_type (limit/category), threshold, period, last_triggered_at

## Flows
1) Record transaction
   - Validate amount/currency
   - Apply 20/80 (or custom ratio per wallet)
   - Optional round-up to nearest unit → adds to savings
   - Persist transaction + update wallet balances atomically
2) Summaries
   - Aggregate last 7/30 days; compute savings rate, category tops, streaks
3) Goals
   - CRUD + progress; auto-allocate savings to goals if configured
4) Nudges/alerts
   - Evaluate rules daily/hourly; enqueue alerts (email/push/SMS via provider)

## API surface (v1 sketch)
- POST `/api/v1/transactions`
- GET `/api/v1/summary?range=7d|30d`
- POST `/api/v1/goals`
- GET `/api/v1/goals`
- GET `/api/v1/nudges`

## Deployment
- Containerized with Gunicorn
- Designed for Cloud Run (stateless) or any OCI host
- Config via env vars; secrets via Secret Manager if on GCP
- Migrations: `python manage.py migrate` on release

## Observability and quality
- Health check endpoint `/healthz`
- Structured JSON logs
- Tests: pytest-django or Django test runner; aim for fast unit coverage on services
