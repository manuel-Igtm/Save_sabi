# Save Sabi - Local Development Setup

This guide walks you through setting up the Save Sabi backend for local development.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or SQLite for quick start)
- Redis 7+ (for Celery)
- Git

## Quick Start (SQLite)

For rapid prototyping without PostgreSQL:

### 1. Clone Repository
```bash
cd Save_sabi/save_sabi
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env - SQLite is default, no changes needed for quick start
```

### 5. Run Migrations
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Start Development Server
```bash
python manage.py runserver
```

The API is now available at `http://localhost:8000/api/v1/`

---

## Full Setup (PostgreSQL + Redis)

For production-like local development:

### 1. Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database
```bash
sudo -u postgres psql
```

```sql
CREATE USER savesabi WITH PASSWORD 'savesabi';
CREATE DATABASE savesabi OWNER savesabi;
\q
```

### 3. Install Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

### 4. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```bash
DEBUG=True
SECRET_KEY=your-dev-secret-key
DATABASE_URL=postgres://savesabi:savesabi@localhost:5432/savesabi
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 5. Run Migrations
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 6. Start Services

**Terminal 1 - Django:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
celery -A save_sabi worker -l info
```

**Terminal 3 - Celery Beat (optional):**
```bash
celery -A save_sabi beat -l info
```

---

## Docker Development

The easiest way to run the full stack:

### 1. Start All Services
```bash
docker-compose up -d
```

This starts:
- Django web server on port 8000
- PostgreSQL on port 5432
- Redis on port 6379
- Celery worker
- Celery beat

### 2. Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 3. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. View Logs
```bash
docker-compose logs -f web  # Django logs
docker-compose logs -f celery_worker  # Celery logs
```

### 5. Stop Services
```bash
docker-compose down
```

### 6. Reset Database
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d
```

---

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=core --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests
```bash
pytest core/tests/test_models.py
pytest core/tests/test_services.py -k "test_split"
pytest -v  # Verbose output
```

---

## Code Quality

### Format Code
```bash
black .
isort .
```

### Lint
```bash
flake8
mypy .
```

---

## Project Structure

```
save_sabi/
├── manage.py                 # Django CLI
├── requirements.txt          # Python dependencies
├── Dockerfile               # Production container
├── docker-compose.yml       # Local development stack
├── .env.example             # Environment template
├── pytest.ini               # Test configuration
│
├── save_sabi/               # Project configuration
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py              # WSGI entry point
│   ├── asgi.py              # ASGI entry point
│   └── celery.py            # Celery configuration
│
├── core/                    # Main application
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Data models
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API views
│   ├── urls.py              # API routes
│   ├── signals.py           # Django signals
│   ├── tasks.py             # Celery tasks
│   ├── exceptions.py        # Custom exceptions
│   ├── permissions.py       # DRF permissions
│   │
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── ledger.py        # Transaction logic
│   │   ├── summaries.py     # Analytics
│   │   ├── goals.py         # Goal tracking
│   │   └── nudges.py        # Budget alerts
│   │
│   ├── repositories/        # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── wallet_repo.py
│   │   └── transaction_repo.py
│   │
│   └── tests/               # Test suite
│       ├── __init__.py
│       ├── factories.py     # Test data factories
│       ├── test_models.py
│       ├── test_services.py
│       └── test_views.py
│
└── docs/                    # Documentation
    ├── API.md
    ├── SETUP.md
    ├── DEPLOYMENT.md
    └── DATABASE.md
```

---

## Common Issues

### Database Connection Error
```
django.db.utils.OperationalError: could not connect to server
```
**Solution:** Ensure PostgreSQL is running:
```bash
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux
```

### Celery Not Processing Tasks
**Solution:** Check Redis is running:
```bash
redis-cli ping  # Should return PONG
```

### Migration Conflicts
```bash
python manage.py migrate --fake
python manage.py makemigrations --merge
```

### Permission Denied on Docker
```bash
sudo chown -R $USER:$USER .
```

---

## Useful Commands

```bash
# Django shell
python manage.py shell_plus

# Database shell
python manage.py dbshell

# Show URLs
python manage.py show_urls

# Generate new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Clear Celery queue
celery -A save_sabi purge
```

---

## IDE Setup

### VS Code Extensions
- Python
- Pylance
- Django
- Docker

### Settings (`.vscode/settings.json`)
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```
