# Deployment Guide for Sprint Assistant Backend

This guide provides instructions for deploying your Sprint Assistant backend to free hosting platforms.

## Option 1: Railway (Recommended)

Railway offers a generous free tier and automatic deployments from GitHub.

### Prerequisites
1. GitHub account
2. Railway account (sign up at https://railway.app)

### Steps

1. **Push your code to GitHub:**
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/sprint-assistant-backend.git
   git push -u origin main
   ```

2. **Deploy to Railway:**
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect the Dockerfile and deploy

3. **Set Environment Variables in Railway:**
   Go to your project settings and add these environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   JIRA_SERVER=https://your-domain.atlassian.net
   JIRA_USERNAME=your-email@domain.com
   JIRA_API_TOKEN=your_jira_api_token
   JIRA_PROJECT_KEY=YOUR_PROJECT
   GITHUB_TOKEN=your_github_token (optional)
   ```

4. **Your API will be available at:**
   ```
   https://your-app-name.railway.app
   ```

## Option 2: Render

Render is another excellent free hosting platform.

### Steps

1. **Push code to GitHub** (same as above)

2. **Deploy to Render:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn sprint_agent_api:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables in Render** (same variables as Railway)

## Option 3: Heroku (has free tier limitations)

### Steps

1. **Install Heroku CLI and login:**
   ```bash
   # Install Heroku CLI (macOS)
   brew tap heroku/brew && brew install heroku
   heroku login
   ```

2. **Create Heroku app:**
   ```bash
   cd backend
   heroku create your-app-name
   ```

3. **Deploy:**
   ```bash
   git push heroku main
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set JIRA_SERVER=https://your-domain.atlassian.net
   # ... add other variables
   ```

## Testing Your Deployment

Once deployed, test your API:

1. **Health check:**
   ```bash
   curl https://your-app-url.com/health
   ```

2. **API documentation:**
   Visit: `https://your-app-url.com/docs`

3. **Test interface:**
   Visit: `https://your-app-url.com/test`

## Environment Variables Required

Make sure to set these environment variables in your hosting platform:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional (can be provided via API calls)
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT
GITHUB_TOKEN=your_github_token
```

## Security Notes

1. **Never commit sensitive information** like API keys to your repository
2. **Use environment variables** for all sensitive configuration
3. **Consider implementing rate limiting** for production use
4. **Update CORS settings** in production to only allow specific origins

## Monitoring

Most platforms provide:
- Application logs
- Performance metrics  
- Uptime monitoring
- Custom domain support (paid plans)

Choose Railway for the easiest deployment experience, or Render if you prefer their interface.
