#!/bin/bash
# Setup script for geo-realistic city generator

echo "🏗️  Setting up Geo-Realistic City Generator..."
echo ""

# Check Python version
echo "📦 Checking Python version..."
python3 --version

# Install backend dependencies
echo ""
echo "📦 Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements-geo.txt

echo ""
echo "✅ Backend dependencies installed"

# Check Blender installation
echo ""
echo "🎨 Checking Blender installation..."
if command -v blender &> /dev/null; then
    echo "✅ Blender found: $(which blender)"
    blender --version
elif [ -f "/Applications/Blender.app/Contents/MacOS/Blender" ]; then
    echo "✅ Blender found: /Applications/Blender.app/Contents/MacOS/Blender"
    /Applications/Blender.app/Contents/MacOS/Blender --version
else
    echo "⚠️  Blender not found!"
    echo "Please install Blender:"
    echo "  brew install --cask blender"
    echo "  OR download from https://www.blender.org/download/"
fi

# Create storage directories
echo ""
echo "📁 Creating storage directories..."
mkdir -p storage/geo_data
mkdir -p storage/models
mkdir -p blender
echo "✅ Directories created"

# Frontend setup
echo ""
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install @react-google-maps/api

echo ""
echo "⚙️  Frontend environment setup..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "VITE_GOOGLE_MAPS_API_KEY=your_api_key_here" > .env
    echo "⚠️  Please update frontend/.env with your Google Maps API key"
else
    echo "✅ .env file exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Get Google Maps API key from: https://console.cloud.google.com/"
echo "2. Update frontend/.env with your API key"
echo "3. Start backend: cd backend && uvicorn app.main:app --reload"
echo "4. Start frontend: cd frontend && npm run dev"
echo "5. Navigate to /city-generator in your app"
echo ""
echo "📚 See CITY_GENERATOR_README.md for detailed documentation"
