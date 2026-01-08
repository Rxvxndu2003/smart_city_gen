# Smart City Planning System - Backend

AI-powered urban planning and design system for Sri Lanka with UDA compliance checking.

## Features

- **FastAPI** backend with async support
- **MySQL** database with SQLAlchemy ORM
- **JWT** authentication with role-based access control (RBAC)
- **ML Models** integration (PyTorch, scikit-learn)
- **Blender** headless 3D generation
- **Multi-step approval workflow** for projects
- **UDA compliance** validation
- **OpenAI GPT** integration for design assistance

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL`: MySQL connection string
- `SECRET_KEY`: JWT secret (min 32 characters)
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_MAPS_API_KEY`: Google Maps API key
- `BLENDER_EXECUTABLE_PATH`: Path to Blender executable

### 3. Set Up Database

```bash
# Create MySQL database
mysql -u root -p -e "CREATE DATABASE smart_city CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations (using Alembic)
alembic upgrade head

# Or for development, let FastAPI create tables
# Set DEBUG=True in .env and run the app
```

### 4. Seed Initial Data

```bash
# Create default roles and admin user
python scripts/seed_data.py
```

### 5. Run the Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/api/docs`

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic
│   ├── repositories/        # Data access layer
│   ├── dependencies/        # FastAPI dependencies (auth, db)
│   ├── middleware/          # Custom middleware
│   ├── utils/               # Utility functions
│   └── workers/             # Background task workers
├── ml_models/               # Trained ML model files
├── blender_scripts/         # Blender generation scripts
├── storage/                 # Generated files and exports
├── tests/                   # Unit and integration tests
└── alembic/                 # Database migrations

```

## ML Models

Place your trained models in `ml_models/`:
- `deployed_model.pt` - PyTorch OSM-based model
- `clf_requires_open_space.pkl` - Open space classifier
- `reg_min_open_space_m2.pkl` - Open space regression
- `feature_columns.json` - Feature schema

## User Roles

- **Admin** - Full system access
- **ProjectOwner** - Create and own projects
- **Architect** - Design and submit layouts
- **Engineer** - Technical review
- **Regulator** - Regulatory approval
- **Contractor** - View approved designs
- **Investor** - View financial data
- **Viewer** - Read-only access

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/logout` - Logout

### Users (Admin only)
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `POST /api/v1/users/{id}/roles/assign` - Assign roles

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project

### Validation
- `POST /api/v1/validation/check` - Run UDA validation
- `GET /api/v1/validation/reports/{id}` - Get validation report

### Generation
- `POST /api/v1/generation/start` - Start 3D generation
- `GET /api/v1/generation/status/{job_id}` - Check generation status

### Approvals
- `GET /api/v1/approvals/pending` - Get pending approvals
- `POST /api/v1/approvals/submit` - Submit for review
- `POST /api/v1/approvals/approve` - Approve layout
- `POST /api/v1/approvals/reject` - Reject layout

### Exports
- `POST /api/v1/exports/generate` - Generate exports (IFC, DXF, etc.)
- `GET /api/v1/exports/{id}/download` - Download export file

### Admin
- `GET /api/v1/admin/dashboard` - Admin dashboard stats
- `GET /api/v1/admin/system-settings` - System settings
- `PUT /api/v1/admin/system-settings` - Update settings

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Development

### Code Style

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Deployment

See `docs/DEPLOYMENT.md` for production deployment instructions.

## License

Proprietary - All rights reserved
