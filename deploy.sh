#!/bin/bash

# Sprint Assistant Backend Deployment Helper
# This script helps with local testing and deployment preparation

echo "🚀 Sprint Assistant Backend Deployment Helper"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "sprint_agent_api.py" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo "🔍 Checking requirements..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
REQUIRED_VERSION="3.12"

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Check if Python version is compatible
if [[ "$PYTHON_VERSION" < "$REQUIRED_VERSION" ]]; then
    echo "⚠️  Warning: Python $REQUIRED_VERSION+ recommended (you have $PYTHON_VERSION)"
fi

if ! command_exists pip; then
    echo "❌ pip is required but not installed"
    exit 1
fi

echo "✅ Python and pip are available"

# Ask user what they want to do
echo ""
echo "What would you like to do?"
echo "1. Install dependencies and test locally"
echo "2. Build Docker image locally"
echo "3. Test Docker container locally"
echo "4. Show deployment instructions"
echo "5. Check environment variables"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "📦 Installing dependencies..."
        
        # Use virtual environment if it exists, otherwise use system pip
        if [ -d ".venv" ]; then
            echo "✅ Using existing virtual environment"
            source .venv/bin/activate
            pip install -r requirements.txt
        else
            echo "🔧 Creating virtual environment..."
            python3 -m venv .venv
            source .venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
        fi
        
        echo ""
        echo "🧪 Running build verification tests..."
        python test_build.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "🚀 Starting local server for testing..."
            echo "API will be available at: http://localhost:8000"
            echo "API docs at: http://localhost:8000/docs"
            echo "Press Ctrl+C to stop"
            echo ""
            uvicorn sprint_agent_api:app --host 127.0.0.1 --port 8000 --reload
        else
            echo "❌ Build verification failed. Please fix issues before running."
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo "🐳 Building Docker image..."
        docker build -t sprint-assistant-backend .
        echo "✅ Docker image built successfully"
        ;;
    
    3)
        echo ""
        echo "🐳 Testing Docker container..."
        echo "Building image with Python 3.12.4..."
        docker build -t sprint-assistant-backend .
        
        echo ""
        echo "🧪 Running build verification in Docker..."
        docker run --rm sprint-assistant-backend python test_build.py
        
        if [ $? -eq 0 ]; then
            echo "Starting container on port 8000..."
            echo "API will be available at: http://localhost:8000"
            echo "Press Ctrl+C to stop"
            docker run -p 8000:8000 --env-file .env sprint-assistant-backend
        else
            echo "❌ Docker build verification failed"
            exit 1
        fi
        ;;
    
    4)
        echo ""
        echo "📋 Deployment Instructions"
        echo "========================="
        echo ""
        echo "Choose a hosting platform:"
        echo ""
        echo "🚂 Railway (Recommended - Free tier available)"
        echo "   1. Push code to GitHub"
        echo "   2. Connect GitHub repo to Railway"
        echo "   3. Set environment variables"
        echo "   4. Deploy automatically"
        echo "   Visit: https://railway.app"
        echo ""
        echo "🎨 Render (Alternative - Free tier available)"
        echo "   1. Push code to GitHub"
        echo "   2. Connect GitHub repo to Render"
        echo "   3. Use: uvicorn sprint_agent_api:app --host 0.0.0.0 --port \$PORT"
        echo "   4. Set environment variables"
        echo "   Visit: https://render.com"
        echo ""
        echo "📖 For detailed instructions, see DEPLOYMENT.md"
        ;;
    
    5)
        echo ""
        echo "🔐 Environment Variables Check"
        echo "============================="
        echo ""
        
        # Check for .env file
        if [ -f ".env" ]; then
            echo "✅ .env file found"
            echo "Variables in .env file:"
            grep -E "^[A-Z_]+" .env | cut -d'=' -f1 | sed 's/^/  - /'
        else
            echo "⚠️  No .env file found"
            echo "Creating template .env file..."
            cat > .env << EOF
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# JIRA Configuration (Optional - can be provided via API)
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_PROJECT_KEY=YOUR_PROJECT

# GitHub Configuration (Optional)
GITHUB_TOKEN=your_github_token_here
EOF
            echo "✅ Template .env file created. Please fill in your values."
        fi
        
        echo ""
        echo "Required for deployment:"
        echo "  - OPENAI_API_KEY (Required)"
        echo "  - JIRA_SERVER (Optional)"
        echo "  - JIRA_USERNAME (Optional)"
        echo "  - JIRA_API_TOKEN (Optional)"
        echo "  - JIRA_PROJECT_KEY (Optional)"
        echo "  - GITHUB_TOKEN (Optional)"
        ;;
    
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
