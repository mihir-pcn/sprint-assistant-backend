#!/bin/bash

# Quick deployment setup for Railway
echo "🚀 Setting up Sprint Assistant for Railway deployment..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    
    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
.coverage
.pytest_cache/
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Virtual environments
venv/
env/
ENV/
EOF
        echo "✅ Created .gitignore"
    fi
fi

# Check if .env exists, if not create from template
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✅ Created .env from template"
        echo "⚠️  Please edit .env with your actual API keys before deploying"
    else
        echo "❌ .env.template not found"
    fi
fi

# Add all files to git
git add .
git commit -m "Initial commit - Sprint Assistant Backend ready for deployment"

echo ""
echo "✅ Setup complete! Your backend is ready for deployment."
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your actual API keys"
echo "2. Create a GitHub repository and push this code:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Railway:"
echo "   - Go to https://railway.app"
echo "   - Connect your GitHub repository"
echo "   - Set environment variables in Railway dashboard"
echo "   - Deploy!"
echo ""
echo "🔗 Your API will be available at: https://your-app-name.railway.app"
echo "📚 API docs at: https://your-app-name.railway.app/docs"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
