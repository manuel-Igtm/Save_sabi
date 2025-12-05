# Save Sabi

**Smart Savings Backend** - A Django + DRF powered API implementing the Hara Hachi Bu 80/20 savings principle with kaizen-style nudges and goal tracking.

## 🎯 Core Concept

Save Sabi automatically splits every income:
- **80%** goes to your spend balance (available for daily use)
- **20%** goes to your savings balance (protected for goals)

Plus intelligent budget rules that nudge you when spending exceeds thresholds.

## ✨ Features

- 🔐 **Token Authentication** - Secure API access
- 💰 **Automatic 80/20 Split** - Every income auto-distributes
- 🔄 **Round-up Savings** - Optional micro-savings on expenses
- 🎯 **Goal Tracking** - Set and track savings goals
- 📊 **Budget Rules** - Category limits, daily limits
- 🔔 **Smart Nudges** - Alerts when you're overspending
- 🔥 **Savings Streaks** - Gamification for consistency
- 📈 **Analytics** - Summaries and category breakdowns

## 🚀 Quick Start

```bash
# Clone and setup
cd save_sabi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env

# Database
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
```

API available at `http://localhost:8000/api/v1/`

## 📚 Documentation

- [API Reference](docs/API.md) - Complete endpoint documentation
- [Setup Guide](docs/SETUP.md) - Local development setup
- [Deployment](docs/DEPLOYMENT.md) - Cloud Run deployment
- [Database](docs/DATABASE.md) - Schema documentation

## 🐳 Docker

```bash
docker-compose up -d
```

## 🧪 Testing

```bash
pytest
pytest --cov=core --cov-report=html
```

## 📁 Project Structure

```
save_sabi/
├── core/              # Main application
│   ├── models.py      # Data models
│   ├── serializers.py # DRF serializers
│   ├── views.py       # API views
│   ├── services/      # Business logic
│   └── tests/         # Test suite
├── docs/              # Documentation
└── docker-compose.yml # Local stack
```

## 🔧 Tech Stack

- **Django 4.2** + **Django REST Framework**
- **PostgreSQL** (production) / SQLite (development)
- **Celery** + **Redis** for background jobs
- **Docker** + **Gunicorn** for deployment
- **Cloud Run** ready

## 📄 License

MIT License - see LICENSE file for details.
