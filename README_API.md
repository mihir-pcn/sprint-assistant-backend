# 🚀 Sprint Agent API - Multi-Agent Development Workflow System

A powerful FastAPI-based multi-agent system that processes natural language requirements and automatically creates JIRA tickets through intelligent agent orchestration.

## 🏗️ Architecture

```
HTTP Request → FastAPI Server → Sprint Agent (Orchestrator)
                                        ↓
                              Analyzes Intent with GPT-4
                                        ↓
        ┌─────────────────────────────────────────────────────┐
        │                                                     │
        ▼                          ▼                         ▼
Requirement Agent          JIRA Agent                GitHub Agent
(Task Creator)            (Ticket Creator)          (PR Tracker)
        │                          │                         │
        ▼                          ▼                         ▼
Generated Tasks  →  JIRA Tickets Created  →  PR Status Checked
                                        │
                                        ▼
                              JSON Response with Results
```

## ✨ Features

- **RESTful API**: Fast, scalable FastAPI server
- **Multi-Agent Orchestration**: AI-powered intelligent routing using LangGraph
- **Natural Language Processing**: GPT-4 powered requirement analysis
- **JIRA Integration**: Automatic ticket creation with rich metadata
- **GitHub Integration**: PR status tracking and linking
- **Health Monitoring**: Comprehensive system health checks
- **Error Handling**: Graceful failure management and reporting
- **Environment Configuration**: Flexible config via env vars or API

## 🛠️ Quick Start

### 1. Start the API Server

```bash
./run_api.sh
```

### 2. Test the API

```bash
# Interactive client
./api_client.py

# Command line
./api_client.py "Create a user authentication system with login and registration"

# Direct HTTP
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "Build a shopping cart with payment integration"}'
```

## 📡 API Endpoints

### Core Processing

- **POST `/process`** - Process natural language requirements
- **GET `/health`** - System health check
- **GET `/`** - API information

### JIRA Integration

- **GET `/tickets`** - Get all JIRA tickets
- **GET `/tickets/{ticket_key}`** - Get specific ticket details

### Documentation

- **GET `/docs`** - Interactive API documentation (Swagger UI)
- **GET `/redoc`** - Alternative API documentation

## 🔧 API Usage Examples

### Process Natural Language Requirement

```bash
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Create a blog system with posts, comments, user authentication, and an admin dashboard",
       "jira_project": "BLOG"
     }'
```

**Response:**

```json
{
  "success": true,
  "message": "Generated 5 tasks; Created 5 JIRA tickets",
  "tasks": [
    "Create blog post model and database schema",
    "Implement user authentication system",
    "Build comment system with moderation",
    "Develop admin dashboard with analytics",
    "Write comprehensive unit tests"
  ],
  "jira_keys": ["BLOG-123", "BLOG-124", "BLOG-125", "BLOG-126", "BLOG-127"],
  "data": {
    "summary": {
      "tasks_generated": 5,
      "tickets_created": 5,
      "errors": 0
    }
  }
}
```

### Check System Health

```bash
curl "http://localhost:8000/health"
```

**Response:**

```json
{
  "status": "healthy",
  "message": "All systems operational",
  "components": {
    "openai": "✅ OK",
    "jira_handler": "✅ OK",
    "langgraph_workflow": "✅ OK",
    "env_openai_api_key": "✅ Set",
    "env_jira_server": "✅ Set"
  }
}
```

### Get All Tickets

```bash
curl "http://localhost:8000/tickets?max_results=10"
```

## 🎯 Agent Behavior

### Sprint Agent (Orchestrator)

- Analyzes user intent using GPT-4
- Routes requests to appropriate specialized agents
- Makes intelligent decisions about workflow execution

### Requirement Agent

- Converts natural language into specific development tasks
- Breaks down complex requirements into actionable items
- Ensures tasks are clear and implementable

### JIRA Agent

- Creates properly formatted JIRA tickets
- Uses advanced JIRA handler for rich metadata
- Handles errors gracefully with fallback mechanisms

### GitHub Agent

- Tracks PR statuses and provides links
- Extracts metadata from GitHub API
- Correlates PRs with JIRA tickets

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
JIRA_SERVER=https://your-company.atlassian.net/
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token

# Optional
JIRA_PROJECT_KEY=TEST
GITHUB_TOKEN=your_github_token
```

### API Request Configuration

You can also provide configuration per request:

```json
{
  "text": "Your requirement here",
  "jira_server": "https://custom.atlassian.net/",
  "jira_username": "custom@email.com",
  "jira_api_token": "custom_token",
  "jira_project": "CUSTOM"
}
```

## 🚀 Installation & Setup

### Automatic Setup

```bash
git clone <repository>
cd "sprint agent"
./run_api.sh
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn sprint_agent_api:app --host 0.0.0.0 --port 8000 --reload
```

## 🧪 Testing

### Using the Python Client

```bash
# Interactive mode
./api_client.py

# Single command
./api_client.py "Create an e-commerce platform with user accounts"

# Health check
python -c "from api_client import test_health; test_health()"
```

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Process requirement
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Build a chat application with real-time messaging"}'

# Get tickets
curl http://localhost:8000/tickets
```

### Using the Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI with interactive testing.

## 📁 Project Structure

```
sprint agent/
├── sprint_agent_api.py      # FastAPI server (NEW)
├── api_client.py            # API test client (NEW)
├── run_api.sh              # API server launcher (NEW)
├── requirements.txt         # Updated dependencies
├── .env                    # Environment configuration
├── README.md               # This documentation
└── jira_agent/             # JIRA integration module
    ├── handler.py          # Advanced JIRA operations
    ├── jira_client.py      # JIRA API client
    ├── models.py           # Data models
    └── config.py           # Configuration management
```

## 🔄 Workflow Examples

### E-commerce Platform

**Input:** `"Create an e-commerce platform with product catalog, shopping cart, payment processing, and order management"`

**Generated Tasks:**

1. Design product catalog with categories and search
2. Implement shopping cart functionality
3. Integrate payment gateway (Stripe/PayPal)
4. Build order management system
5. Create user account and profile management
6. Implement inventory tracking
7. Add email notifications for orders
8. Write comprehensive tests

**Result:** 8 JIRA tickets created automatically

### Mobile App Backend

**Input:** `"Build a REST API for a social media mobile app with posts, likes, comments, and push notifications"`

**Generated Tasks:**

1. Design REST API endpoints for posts
2. Implement user authentication with JWT
3. Create like/unlike functionality
4. Build commenting system with threading
5. Integrate push notification service
6. Add image upload and processing
7. Implement feed algorithm
8. Set up API rate limiting and security

## 🔒 Security Features

- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive error management
- **API Rate Limiting**: Built-in FastAPI protections
- **Credential Management**: Secure environment variable handling
- **Logging**: Detailed operation logging for monitoring

## 🐛 Troubleshooting

### Common Issues

#### 1. Server Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Use different port
uvicorn sprint_agent_api:app --port 8001
```

#### 2. JIRA Authentication Errors

- Verify JIRA server URL format: `https://company.atlassian.net/`
- Check API token is valid and not expired
- Ensure email matches JIRA account

#### 3. OpenAI API Errors

- Verify API key is valid: `echo $OPENAI_API_KEY`
- Check API quota and billing status
- Test with simple request first

#### 4. Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Debug Mode

Set environment variable for detailed logging:

```bash
export LOG_LEVEL=DEBUG
```

### Health Check

Always start troubleshooting with:

```bash
curl http://localhost:8000/health
```

## 📊 Performance

- **Concurrent Requests**: FastAPI handles multiple simultaneous requests
- **Response Time**: Typically 2-5 seconds for requirement processing
- **Scalability**: Horizontal scaling ready with load balancers
- **Memory Usage**: ~100MB base + ~50MB per concurrent request

## 🤝 API Integration

### Python

```python
import requests

def create_tickets(requirement: str):
    response = requests.post(
        "http://localhost:8000/process",
        json={"text": requirement}
    )
    return response.json()

result = create_tickets("Build a file upload service")
print(f"Created tickets: {result['jira_keys']}")
```

### JavaScript

```javascript
async function createTickets(requirement) {
  const response = await fetch("http://localhost:8000/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: requirement }),
  });
  return await response.json();
}

const result = await createTickets("Build a notification system");
console.log("Created tickets:", result.jira_keys);
```

## 📈 Monitoring

The API provides comprehensive monitoring through:

- Health check endpoint (`/health`)
- Structured logging to stdout
- Performance metrics in responses
- Error tracking and reporting

## 🚀 Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "sprint_agent_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```bash
OPENAI_API_KEY=prod_key
JIRA_SERVER=https://prod.atlassian.net/
JIRA_USERNAME=prod@company.com
JIRA_API_TOKEN=prod_token
JIRA_PROJECT_KEY=PROD
LOG_LEVEL=INFO
```

---

**🎉 Happy API Development with Sprint Agent!**

For more examples and advanced usage, visit the interactive documentation at `http://localhost:8000/docs` when the server is running.
