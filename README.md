# 🤖 Sprint Agent - Multi-Agent System for Development Management

A powerful multi-agent system built with LangGraph and Streamlit that orchestrates requirement analysis, JIRA ticket creation, and GitHub PR status tracking.

## 🚀 Features

- **Multi-Agent Architecture**: Uses LangGraph to orchestrate multiple specialized agents
- **Requirement Agent**: Converts natural language requirements into development tasks
- **JIRA Agent**: Automatically creates JIRA tickets from tasks
- **GitHub Agent**: Tracks PR statuses and provides links
- **Sprint Assistant**: AI-powered orchestrator that decides which agents to invoke
- **Streamlit UI**: User-friendly web interface for interaction

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Sprint Agent   │───▶│ Requirement Agent │───▶│   JIRA Agent    │
│  (Orchestrator) │    │  (Task Creator)   │    │ (Ticket Creator)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                              ┌─────────────────┐
│  GitHub Agent   │                              │  Created Tickets │
│ (PR Tracker)    │                              │   TEST-123      │
└─────────────────┘                              │   TEST-124      │
                                                  └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key
- JIRA Account with API Token
- GitHub Account with Personal Access Token (optional)

## 🛠️ Installation

### Option 1: Quick Start (Recommended)

```bash
cd "sprint agent"
./run.sh
```

### Option 2: Manual Setup

1. **Clone or navigate to the project directory:**

   ```bash
   cd "sprint agent"
   ```

2. **Create virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run sprint_agent.py
   ```

## ⚙️ Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# JIRA Configuration
JIRA_SERVER=https://your-company.atlassian.net/
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# GitHub Configuration (Optional)
GITHUB_TOKEN=your_github_token
```

### Getting API Tokens

#### JIRA API Token:

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token
3. Copy the token for configuration

#### OpenAI API Key:

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Copy the key for configuration

#### GitHub Token (Optional):

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate new token with repo permissions
3. Copy the token for configuration

## 🎯 Usage

1. **Start the application:**

   ```bash
   ./run.sh
   ```

2. **Configure credentials** in the sidebar (or use environment variables)

3. **Login** by clicking the "Login with Jira & GitHub" button

4. **Interact with the agent** using natural language:

### Example Interactions:

#### Creating Tasks from Requirements:

```
"Create a user authentication system with login, logout, and password reset functionality"
```

#### Checking JIRA Status:

```
"Show me the status of tickets in project TEST"
```

#### Checking PR Status:

```
"What's the status of PR #123?"
```

## 🧠 How It Works

### 1. User Input Processing

- User enters natural language requirement or query
- Sprint Agent (orchestrator) analyzes the intent using GPT-4

### 2. Agent Routing

The Sprint Agent decides which specialized agent to invoke:

- **RequirementAgent**: For creating tasks from requirements
- **JiraAgent**: For JIRA ticket operations
- **GitAgent**: For GitHub PR status checks

### 3. Task Execution

- **Requirement Agent**: Breaks down requirements into actionable tasks
- **JIRA Agent**: Creates tickets in your JIRA project
- **GitHub Agent**: Fetches PR status and metadata

### 4. Response Generation

- Results are formatted and displayed in the chat interface
- Links to created tickets and PRs are provided

## 📁 Project Structure

```
sprint agent/
├── sprint_agent.py           # Main application
├── requirements.txt          # Python dependencies
├── run.sh                   # Quick start script
├── .env                     # Environment variables (optional)
├── venv/                    # Virtual environment
└── jira_agent/              # JIRA agent module
    ├── config.py            # Configuration management
    ├── handler.py           # Main handler interface
    ├── jira_agent.py        # JIRA operations
    ├── jira_client.py       # JIRA API client
    ├── json_processor.py    # JSON processing
    ├── models.py            # Data models
    ├── requirements.txt     # JIRA agent dependencies
    └── README.md           # JIRA agent documentation
```

## 🔧 Customization

### Adding New Agents

1. **Create agent function:**

   ```python
   def new_agent_fn(state: AgentState) -> AgentState:
       # Your agent logic here
       return {**state, "new_field": "value"}
   ```

2. **Update the orchestrator:**

   ```python
   # Add new condition in sprint_agent_fn
   elif next_agent == "NewAgent":
       state = new_agent_fn(state)
   ```

3. **Update the response formatting** to display new agent results

### Modifying Task Generation

Edit the prompt in `requirement_agent_fn()` to change how requirements are converted to tasks.

### Customizing JIRA Integration

Modify `create_jira_ticket()` to add custom fields, labels, or issue types.

## 🐛 Troubleshooting

### Common Issues:

#### 1. Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. JIRA Authentication Failed

- Verify JIRA server URL (include trailing slash)
- Check API token is valid
- Ensure email matches JIRA account

#### 3. OpenAI API Errors

- Verify API key is valid
- Check API quota/billing
- Ensure internet connectivity

#### 4. Streamlit Port Issues

```bash
# Use different port if 8501 is busy
streamlit run sprint_agent.py --server.port 8502
```

### Debug Mode

Add this to see detailed error messages:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Regularly rotate API tokens
- Keep dependencies updated

## 📝 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review error messages in the terminal
3. Ensure all dependencies are installed correctly

---

**Happy Sprint Management! 🎉**
