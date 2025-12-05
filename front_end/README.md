# Save Sabi - Smart Savings Platform

**Hara Hachi Bu 80/20 Savings with Kaizen Nudges**

A full-stack micro-savings finance application implementing intelligent savings automation with the 80/20 principle, goal tracking, and behavioral nudges to build better financial habits.

- **Backend**: Django REST Framework API
- **Frontend**: React + Vite + TailwindCSS

---

## 🎯 What is Save Sabi?

Save Sabi helps users save money effortlessly by automatically splitting every income:
- **80%** → Spend balance (available for daily expenses)
- **20%** → Savings balance (protected for goals)

The platform uses **kaizen-style nudges** (continuous improvement alerts) to guide users toward better spending habits without being intrusive.

---

## ✨ Key Features

### Core Functionality
- 🔐 **Token-based Authentication** - Secure API access with DRF
- 💰 **Automatic 80/20 Split** - Every income transaction auto-distributes
- 🔄 **Round-up Savings** - Optional micro-savings on expenses (round to nearest unit)
- 🎯 **Savings Goals** - Create, track, and achieve financial goals
- 📊 **Budget Rules** - Set category limits, daily spending caps
- 🔔 **Smart Nudges** - Intelligent alerts when approaching limits
- 🔥 **Savings Streaks** - Gamification to encourage consistency
- 📈 **Analytics & Summaries** - 7-day and 30-day spending insights

### Technical Features
- 🏗️ **Repository Pattern** - Clean architecture with swappable data backends
- 🔄 **Service Layer** - Business logic separated from API layer
- 🧪 **Comprehensive Tests** - pytest-django with coverage reporting
- 🐳 **Docker Support** - Full containerization with docker-compose
- ☁️ **Cloud-Ready** - Designed for Google Cloud Run deployment
- 🔧 **CI/CD Pipeline** - Jenkins pipeline with automated testing and deployment
- 📱 **Mobile-First UI** - Responsive React frontend with modern fintech design

---

## 📁 Project Structure

```
Save_sabi/
├── save_sabi/                 # Django Backend
│   ├── core/                  # Main application module
│   │   ├── models.py          # Data models (Wallet, Transaction, Goal, etc.)
│   │   ├── serializers.py     # DRF serializers for API
│   │   ├── views.py           # API viewsets and endpoints
│   │   ├── services/          # Business logic layer
│   │   │   ├── ledger.py      # Transaction processing & 80/20 split
│   │   │   ├── goals.py       # Goal management
│   │   │   ├── nudges.py      # Budget rules & alert generation
│   │   │   └── summaries.py   # Analytics & reporting
│   │   ├── repositories/      # Data access layer (Repository pattern)
│   │   │   ├── base.py        # Abstract repository interface
│   │   │   ├── wallet_repo.py # Wallet data access
│   │   │   └── transaction_repo.py # Transaction data access
│   │   ├── tasks.py           # Celery background tasks
│   │   └── tests/             # Test suite
│   ├── save_sabi/             # Django project settings
│   ├── docs/                  # Documentation
│   │   ├── API.md             # API reference
│   │   ├── ARCHITECHTURE.md   # Architecture overview
│   │   ├── DATABASE.md        # Database schema
│   │   ├── DEPLOYMENT.md      # Cloud deployment guide
│   │   └── SETUP.md           # Local development setup
│   ├── Dockerfile             # Production container image
│   ├── docker-compose.yml     # Local development stack
│   └── requirements.txt       # Python dependencies
├── src/                       # React Frontend
│   ├── components/            # Reusable UI components
│   │   ├── BalanceCard.jsx
│   │   ├── GoalProgressBar.jsx
│   │   ├── AlertBanner.jsx
│   │   ├── TransactionItem.jsx
│   │   ├── QuickAddModal.jsx
│   │   └── GoalModal.jsx
│   ├── pages/                 # Page components
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   └── History.jsx
│   ├── context/               # React Context
│   │   └── WalletContext.jsx
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── terraform/                 # Infrastructure as Code (IaC)
│   ├── modules/               # Terraform modules
│   │   ├── networking/        # VPC, subnets, firewall
│   │   └── storage/           # Cloud Storage buckets
│   └── README.md              # Terraform documentation
├── scripts/                   # Deployment scripts
│   ├── deploy.sh              # Cloud Run deployment
│   ├── gcp-setup.sh           # GCP project setup
│   └── setup-migration-job.sh # Database migration job
├── Jenkinsfile                # CI/CD pipeline definition
├── package.json               # Frontend dependencies
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Backend Setup (Django API)

#### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or use SQLite for development)
- Redis (for Celery tasks)
- Docker & Docker Compose (optional)

#### Local Development

```bash
# Navigate to backend directory
cd save_sabi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

API will be available at: `http://localhost:8000/api/v1/`

#### Using Docker

```bash
# Start all services (Django, PostgreSQL, Redis, Celery)
docker-compose up -d

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Frontend Setup (React App)

#### Prerequisites
- Node.js 18+ and npm

#### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The dev server will start at `http://localhost:5173/`

#### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

---

## 🏗️ Architecture

### Full Stack Architecture

```
┌─────────────────────────────────────────────────┐
│         React Frontend (Vite + Tailwind)        │
│  • Login, Dashboard, Transaction History        │
│  • Real-time balance updates                    │
│  • Mobile-first responsive design               │
└────────────────┬────────────────────────────────┘
                 │ HTTP/REST API
┌────────────────▼────────────────────────────────┐
│          API Layer (Django REST Framework)      │
│  • Token Authentication                         │
│  • ViewSets for CRUD operations                 │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Service Layer (Business Logic)             │
│  • ledger.py - Transaction processing           │
│  • goals.py - Goal management                   │
│  • nudges.py - Alert generation                 │
│  • summaries.py - Analytics                     │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│   Repository Layer (Data Access Abstraction)    │
│  • Abstract interface (base.py)                 │
│  • PostgreSQL implementation                    │
│  • Firestore-ready design                       │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Data Layer (Django ORM + PostgreSQL)    │
└─────────────────────────────────────────────────┘
```

### Repository Pattern

The application uses the **Repository Pattern** to abstract data access:

- **BaseRepository**: Abstract interface defining CRUD operations
- **WalletRepository**: Wallet data access with balance management
- **TransactionRepository**: Transaction queries with filtering

This design allows swapping PostgreSQL for Firestore or other backends without changing business logic.

### Key Models

- **User**: Extended Django user model
- **Wallet**: User's financial account (savings + spend balances)
- **Transaction**: Income/expense records with automatic 80/20 split
- **Goal**: Savings targets with progress tracking
- **BudgetRule**: Spending limits and thresholds
- **Nudge**: Generated alerts based on budget rules
- **SavingsStreak**: Gamification for consistent saving

---

## 📚 Documentation

Comprehensive documentation is available in the `save_sabi/docs/` directory:

- **[API Reference](save_sabi/docs/API.md)** - Complete endpoint documentation with examples
- **[Architecture](save_sabi/docs/ARCHITECHTURE.md)** - System design and component overview
- **[Database Schema](save_sabi/docs/DATABASE.md)** - Data model documentation
- **[Deployment Guide](save_sabi/docs/DEPLOYMENT.md)** - Cloud Run deployment instructions
- **[Setup Guide](save_sabi/docs/SETUP.md)** - Local development environment setup

---

## 🎨 Frontend Features

### Pages & Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `Login.jsx` | Authentication entry point |
| `/dashboard` | `Dashboard.jsx` | Main app screen with balance, goals, transactions |
| `/history` | `History.jsx` | Full transaction history with filters and export |

### UI Components

- **BalanceCard** - Displays total, savings, and spendable balances
- **GoalProgressBar** - Visual progress toward savings goals
- **AlertBanner** - Budget alerts and notifications
- **TransactionItem** - Individual transaction display
- **QuickAddModal** - Add income/expense transactions
- **GoalModal** - Create and edit savings goals

### Tailwind Theme

```javascript
colors: {
  'sabi-green': '#48BB78',   // Primary color
  'sabi-dark': '#1A202C',    // Text color
  'sabi-light': '#F7FAFC',   // Background
  'sabi-gray': '#718096',    // Secondary text
}
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest core/tests/test_ledger.py

# Run with verbose output
pytest -v
```

### Test Coverage
- Unit tests for all services
- Repository layer tests
- API endpoint tests
- Integration tests with test database

---

## 🚀 Deployment

### Google Cloud Run (Recommended)

The application is designed for serverless deployment on Google Cloud Run:

```bash
# Setup GCP project and enable APIs
./scripts/gcp-setup.sh

# Deploy to Cloud Run
./scripts/deploy.sh
```

See [Deployment Guide](save_sabi/docs/DEPLOYMENT.md) for detailed instructions.

### CI/CD Pipeline

The project includes a Jenkins pipeline (`Jenkinsfile`) that:
1. ✅ Runs linting (flake8, black, isort)
2. ✅ Executes test suite with coverage
3. ✅ Performs security scanning (safety, bandit)
4. ✅ Builds Docker image
5. ✅ Pushes to Google Container Registry
6. ✅ Deploys to Cloud Run (staging/production)

---

## 🔧 Tech Stack

### Backend
- **Django 4.2** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL 15** - Primary database
- **Redis** - Caching and Celery broker
- **Celery** - Background task processing

### Frontend
- **React 18** - UI framework
- **Vite** - Fast build tool and dev server
- **React Router v6** - Page navigation
- **TailwindCSS** - Utility-first CSS framework
- **PostCSS** - CSS processing

### Infrastructure
- **Docker** - Containerization
- **Gunicorn** - WSGI server
- **Google Cloud Run** - Serverless deployment
- **Cloud SQL** - Managed PostgreSQL
- **Secret Manager** - Credentials storage
- **Cloud Storage** - Static/media files

### Development Tools
- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Linting
- **isort** - Import sorting
- **mypy** - Type checking

---

## 🌍 Environment Variables

### Backend (.env)

```bash
# Django Core
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,.run.app

# Database
DATABASE_URL=postgres://user:password@localhost:5432/save_sabi

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Google Cloud (Production)
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=your-bucket-name

# Application Settings
DEFAULT_SAVINGS_RATIO=20
ENABLE_ROUND_UP=True
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Quality Standards
- Follow PEP 8 style guide (backend)
- Follow React best practices (frontend)
- Write tests for new features
- Maintain >80% code coverage
- Use type hints where appropriate
- Document complex logic

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Team

Developed for the ALX Hackathon Project

---

## 🔗 Links

- **API Documentation**: `/api/v1/` (when server is running)
- **Admin Panel**: `/admin/`
- **Health Check**: `/healthz`
- **Frontend App**: `http://localhost:5173/` (development)

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the [documentation](save_sabi/docs/)
- Review the [API reference](save_sabi/docs/API.md)

---

## 🌐 Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 12+
- Mobile browsers (iOS Safari, Chrome Mobile)

---

**Save Sabi** - Building better financial habits, one transaction at a time. 💰✨

**Built with ❤️ using Django, React, Vite, and TailwindCSS**
