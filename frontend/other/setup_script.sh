#!/bin/bash

# Veritas Sentinel Frontend Setup Script
# This script automates the initial setup process

echo "🛡️  Veritas Sentinel Frontend Setup"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "setup.sh" ]; then
    echo -e "${RED}❌ Please run this script from the frontend directory${NC}"
    exit 1
fi

echo "📁 Creating directory structure..."
mkdir -p css js

echo ""
echo "✅ Directories created!"
echo ""

# Check for required files
echo "🔍 Checking for required files..."
required_files=(
    "index.html"
    "login.html"
    "admin_dashboard.html"
    "user_dashboard.html"
    "css/login.css"
    "css/admin_dashboard.css"
    "css/user_dashboard.css"
    "js/config.js"
    "js/login.js"
    "js/admin_dashboard.js"
    "js/user_dashboard.js"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Missing files:${NC}"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please ensure all files are in place before continuing."
    echo ""
else
    echo -e "${GREEN}✅ All required files found!${NC}"
    echo ""
fi

# API Configuration
echo "⚙️  API Configuration"
echo "-------------------"
read -p "Enter your backend API URL [http://localhost:8000]: " api_url
api_url=${api_url:-http://localhost:8000}

# Update config.js
if [ -f "js/config.js" ]; then
    sed -i.bak "s|API_BASE_URL: '.*'|API_BASE_URL: '$api_url'|" js/config.js
    echo -e "${GREEN}✅ Updated API URL in config.js${NC}"
else
    echo -e "${YELLOW}⚠️  config.js not found, skipping API configuration${NC}"
fi

echo ""

# Check for Python
echo "🐍 Checking for Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✅ Python 3 found${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}✅ Python found${NC}"
else
    echo -e "${RED}❌ Python not found${NC}"
    PYTHON_CMD=""
fi

echo ""

# Check for Node.js
echo "📦 Checking for Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js found: $NODE_VERSION${NC}"
    HAS_NODE=true
else
    echo -e "${YELLOW}⚠️  Node.js not found${NC}"
    HAS_NODE=false
fi

echo ""
echo "🚀 Setup Complete!"
echo "================="
echo ""

# Provide next steps
echo "📋 Next Steps:"
echo ""

if [ -n "$PYTHON_CMD" ]; then
    echo "To start the development server with Python:"
    echo -e "${GREEN}   $PYTHON_CMD -m http.server 5173${NC}"
    echo ""
fi

if [ "$HAS_NODE" = true ]; then
    echo "Or with Node.js http-server:"
    echo -e "${GREEN}   npx http-server -p 5173 -c-1${NC}"
    echo ""
fi

echo "Then open your browser to:"
echo -e "${GREEN}   http://localhost:5173/index.html${NC}"
echo ""

echo "📚 Don't forget to:"
echo "   1. Start your backend API on $api_url"
echo "   2. Ensure MongoDB is running"
echo "   3. Create an admin user (see DEPLOYMENT_GUIDE.md)"
echo ""

# Ask if user wants to start server now
if [ -n "$PYTHON_CMD" ]; then
    echo ""
    read -p "Would you like to start the Python HTTP server now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🌐 Starting server on http://localhost:5173"
        echo "   Press Ctrl+C to stop"
        echo ""
        $PYTHON_CMD -m http.server 5173
    fi
fi

echo ""
echo "✨ Happy fraud detecting! ✨"