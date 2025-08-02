# Sprint Agent API Testing Environment

🚀 **Complete API testing environment for your multi-agent Sprint system!**

## Quick Start

### 1. Launch the Testing Environment

```bash
./start_testing.sh
```

This will start the FastAPI server and make all endpoints available.

### 2. Access the Testing Interface

Open your browser and go to: **http://127.0.0.1:8000/test**

## Available Endpoints

| Endpoint   | Method | Description                                   |
| ---------- | ------ | --------------------------------------------- |
| `/`        | GET    | API information and available endpoints       |
| `/test`    | GET    | **Interactive testing interface**             |
| `/health`  | GET    | System health check (OpenAI, JIRA, LangGraph) |
| `/process` | POST   | Process natural language requirements         |
| `/docs`    | GET    | Interactive API documentation (Swagger)       |
| `/redoc`   | GET    | Alternative API documentation                 |

## Testing Interface Features

### 🏥 Health Check

- **Real-time system status monitoring**
- Check OpenAI, JIRA, and LangGraph connectivity
- Environment variable validation
- Component health indicators

### ⚡ Process Requirements

- **Natural language input processing**
- Pre-built example requirements
- Real-time processing feedback
- Detailed task breakdown display
- JIRA ticket creation tracking
- Processing time monitoring

### 📚 API Documentation

- Direct links to Swagger UI and ReDoc
- Interactive API testing
- Request/response examples

## Example Requirements to Test

Click any of these in the testing interface:

### 🔐 User Authentication System

```
Build a user authentication system with login, signup, password reset, and email verification functionality
```

### 💬 Real-time Chat Application

```
Create a real-time chat application with message history, file sharing, and user presence indicators
```

### 🛒 E-commerce REST API

```
Implement a REST API for e-commerce with product catalog, shopping cart, and payment processing
```

### 📊 Task Management System

```
Build a task management system with kanban boards, time tracking, and team collaboration features
```

### 📈 Analytics Dashboard

```
Create a data analytics dashboard with charts, filtering, and export capabilities
```

## How It Works

1. **Input**: Enter natural language requirements
2. **AI Analysis**: OpenAI GPT-4 analyzes and breaks down requirements
3. **Task Generation**: Multi-agent system creates detailed development tasks
4. **JIRA Integration**: Automatically creates tickets in your JIRA instance
5. **Results**: View generated tasks and created ticket IDs

## System Status Indicators

- 🟢 **Healthy**: All systems operational
- 🟡 **Degraded**: Some components have issues
- 🔴 **Error**: System unavailable

## Manual API Testing

### Using curl:

```bash
# Health check
curl http://127.0.0.1:8000/health

# Process a requirement
curl -X POST http://127.0.0.1:8000/process \
  -H "Content-Type: application/json" \
  -d '{"requirement": "Build a user dashboard with analytics"}'
```

### Using Python:

```python
import requests

# Health check
response = requests.get("http://127.0.0.1:8000/health")
print(response.json())

# Process requirement
data = {"requirement": "Create a mobile app for task management"}
response = requests.post("http://127.0.0.1:8000/process", json=data)
print(response.json())
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │───▶│   FastAPI Server │───▶│  Multi-Agent    │
│                 │    │                  │    │   System        │
│ Testing Interface│    │  • CORS enabled │    │                 │
│ • Health Check   │    │  • JSON API      │    │ • RequirementAgent │
│ • Process Reqs   │    │  • Static files  │    │ • JiraAgent     │
│ • Real-time UI   │    │  • Error handling│    │ • LangGraph     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        │
                                │                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Environment    │    │  External APIs  │
                       │                  │    │                 │
                       │ • OpenAI API Key │    │ • OpenAI GPT-4  │
                       │ • JIRA Config    │    │ • JIRA REST API │
                       │ • .env file      │    │ • Ticket Creation│
                       └──────────────────┘    └─────────────────┘
```

## Troubleshooting

### Server won't start

1. Check if virtual environment is activated: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Verify environment variables in `.env` file

### API requests fail

1. Ensure server is running on port 8000
2. Check CORS settings allow your browser
3. Verify API endpoints in browser dev tools

### JIRA tickets not created

1. Check JIRA credentials in `.env` file
2. Verify JIRA permissions for API token
3. Check JIRA project key exists

### OpenAI errors

1. Verify OPENAI_API_KEY is valid
2. Check API quota/billing status
3. Test with smaller requirements first

## Development

### Adding new endpoints:

1. Edit `sprint_agent_api.py`
2. Add endpoint function with `@app.get()` or `@app.post()`
3. Server auto-reloads with `--reload` flag

### Modifying the testing interface:

1. Edit `api_test_interface.html`
2. Changes are served immediately
3. Refresh browser to see updates

## Files Overview

- `sprint_agent_api.py` - Main FastAPI server
- `api_test_interface.html` - Web testing interface
- `start_testing.sh` - Launch script
- `.env` - Environment variables
- `jira_agent/` - JIRA integration module
- `requirements.txt` - Python dependencies

---

**🎯 Your Sprint Agent API is ready for testing!**

Access the testing interface at: http://127.0.0.1:8000/test
