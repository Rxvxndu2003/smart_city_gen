#!/bin/bash

# Smart City Quick Start Script
# This script helps you get started with the development environment

set -e  # Exit on error

echo "======================================"
echo "🏙️  Smart City - Quick Start"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if MySQL is installed
echo "🔍 Checking MySQL..."
if command -v mysql &> /dev/null; then
    echo -e "${GREEN}✅ MySQL is installed${NC}"
else
    echo -e "${YELLOW}⚠️  MySQL not found${NC}"
    echo ""
    echo "Please install MySQL first:"
    echo "  brew install mysql"
    echo "  brew services start mysql"
    echo ""
    echo "Or use Docker:"
    echo "  docker-compose up -d"
    exit 1
fi

# Check if database exists
echo ""
echo "🔍 Checking database..."
if mysql -u root -e "USE smart_city" 2>/dev/null; then
    echo -e "${GREEN}✅ Database 'smart_city' exists${NC}"
else
    echo -e "${YELLOW}📝 Creating database 'smart_city'...${NC}"
    mysql -u root -e "CREATE DATABASE smart_city CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" || {
        echo -e "${RED}❌ Failed to create database${NC}"
        echo "Please run:"
        echo "  mysql -u root -p"
        echo "  CREATE DATABASE smart_city CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        exit 1
    }
    echo -e "${GREEN}✅ Database created${NC}"
fi

# Backend setup
echo ""
echo "🔧 Setting up backend..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install core dependencies
echo "📦 Installing backend dependencies (this may take a few minutes)..."
pip install --upgrade pip setuptools wheel -q
pip install fastapi uvicorn sqlalchemy pymysql alembic python-dotenv pydantic pydantic-settings python-jose passlib python-multipart cryptography -q

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file - please update with your settings${NC}"
fi

# Initialize Alembic if not already done
if [ ! -d "alembic" ]; then
    echo "🗄️  Initializing Alembic..."
    alembic init alembic
    echo "📝 Configuring Alembic..."
    python scripts/setup_alembic.py
fi

# Create initial migration if none exist
if [ ! "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "📝 Creating initial database migration..."
    alembic revision --autogenerate -m "Initial migration"
fi

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Create admin user if needed
echo ""
read -p "📝 Create admin user and test users? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/create_admin.py
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ Backend setup complete!${NC}"
echo "======================================"

# Frontend setup
cd ../frontend
echo ""
echo "🔧 Setting up frontend..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ Frontend setup complete!${NC}"
echo "======================================"

# Final instructions
cd ..
echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "4. Login with:"
echo "   Email: admin@smartcity.lk"
echo "   Password: admin123"
echo ""
echo -e "${YELLOW}⚠️  Remember to change the admin password!${NC}"
echo ""
