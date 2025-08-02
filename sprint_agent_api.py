from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from typing import TypedDict
from jira import JIRA
from github import Github
from openai import OpenAI
from langchain_core.runnables import RunnableLambda, RunnableBranch
from datetime import datetime
import os
import sys
import logging
from contextlib import asynccontextmanager

# Add jira_agent to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'jira_agent'))

# Try to load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, skip
    pass

# Import jira_agent components
try:
    from jira_agent import JiraHandler
    from jira_agent.models import TicketRequest, TicketInfo
    from jira_agent.config import Config
except ImportError as e:
    logging.warning(f"Could not import jira_agent components: {e}")
    JiraHandler = None
    TicketRequest = None
    TicketInfo = None
    Config = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Pydantic Models for API ===
class ProcessRequestModel(BaseModel):
    requirement: str
    jira_server: Optional[str] = None
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_project: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None

class ProcessResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    tasks: Optional[List[str]] = None
    jira_keys: Optional[List[str]] = None
    pr_statuses: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class HealthResponseModel(BaseModel):
    status: str
    message: str
    components: Dict[str, str]

# === LangGraph Agent State ===
class AgentState(TypedDict):
    user_input: str
    intermediate_result: Any
    agent_queue: List[str]
    agent_logs: List[str]
    agent_results: Dict[str, Any]
    jira_domain: str
    jira_email: str
    jira_token: str
    jira_project: str
    github_token: str
    github_repo: str
    __next__: str

# Global variables
app_state = {
    "jira_handler": None,
    "workflow": None,
    "openai_client": None
}

# === OpenAI Client ===
def get_openai_client():
    """Get OpenAI client with API key validation."""
    if app_state["openai_client"]:
        return app_state["openai_client"]
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    app_state["openai_client"] = OpenAI(api_key=openai_api_key)
    return app_state["openai_client"]

# === JIRA + GitHub Functions ===
def create_jira_ticket(summary, description, state: AgentState):
    """Create JIRA ticket using the jira_agent handler."""
    try:
        if app_state["jira_handler"]:
            # Use the advanced jira_agent handler
            ticket_request = TicketRequest(
                summary=summary,
                description=description,
                project_key=state["jira_project"],
                issue_type="Task"
            )
            result = app_state["jira_handler"].jira_agent._handle_create_action(ticket_request)
            if result.get('success'):
                return result['data']['ticket_key']
            else:
                logger.error(f"JIRA handler failed: {result.get('error')}")
                raise Exception(result.get('error', 'Unknown error'))
        else:
            # Fallback to direct JIRA API
            jira = JIRA(server=state["jira_domain"], basic_auth=(state["jira_email"], state["jira_token"]))
            issue_dict = {
                'project': {'key': state["jira_project"]},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Task'},
            }
            issue = jira.create_issue(fields=issue_dict)
            return issue.key
    except Exception as e:
        logger.error(f"Error creating JIRA ticket: {str(e)}")
        return f"ERROR: {str(e)}"

def get_pr_status(pr_number: int, state: AgentState):
    """Get GitHub PR status."""
    try:
        github = Github(state["github_token"])
        repo = github.get_repo(state["github_repo"])
        pr = repo.get_pull(pr_number)
        return {
            "title": pr.title,
            "state": pr.state,
            "merged": pr.is_merged(),
            "url": pr.html_url
        }
    except Exception as e:
        return {"error": str(e), "pr_number": pr_number}

# === Agent Implementations ===
def requirement_agent_fn(state: AgentState) -> AgentState:
    """Convert requirements to development tasks."""
    try:
        client = get_openai_client()
        prompt = f"""Convert the following requirement into a list of development tasks:

{state['intermediate_result']}

Return as a numbered list of specific, actionable development tasks. Each task should be:
- Clear and specific
- Implementable by a developer
- Focused on a single feature or component
- Include testing where appropriate

Format: Return only the numbered list, one task per line."""

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        raw = response.choices[0].message.content.strip().split("\n")
        tasks = []
        for line in raw:
            clean_line = line.strip()
            # Remove numbering and bullet points
            clean_line = clean_line.lstrip("0123456789.•-* ").strip()
            if clean_line and any(c.isalpha() for c in clean_line):
                tasks.append(clean_line)
        
        state["intermediate_result"] = tasks
        state["agent_results"]["RequirementAgent"] = tasks
        state["agent_logs"].append(f"RequirementAgent generated {len(tasks)} tasks.")
        logger.info(f"RequirementAgent generated {len(tasks)} tasks")
        
    except Exception as e:
        logger.error(f"RequirementAgent error: {e}")
        state["agent_logs"].append(f"RequirementAgent error: {e}")
    
    # Move to next agent in queue
    state["__next__"] = state["agent_queue"].pop(0) if state["agent_queue"] else "END"
    return state

def jira_agent_fn(state: AgentState) -> AgentState:
    """Create JIRA tickets from tasks with AI-generated descriptions."""
    try:
        tasks = state.get("intermediate_result", [])
        if not tasks:
            state["agent_logs"].append("JiraAgent skipped (no tasks to create).")
        else:
            keys = []
            client = get_openai_client()
            
            # Generate all descriptions in one API call for efficiency
            logger.info(f"Generating descriptions for {len(tasks)} tasks...")
            tasks_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
            
            bulk_prompt = f"""Create detailed professional JIRA descriptions for these development tasks:

{tasks_list}

Context: {state.get('user_input', 'Not specified')}

For each task, provide a comprehensive description with:
- **Overview**: Detailed explanation of what needs to be done (3-4 sentences)
- **Background**: Why this task is important and how it fits into the project (2-3 sentences)
- **Implementation Details**: Key technical approach and considerations (3-4 sentences)
- **Acceptance Criteria**: Specific, testable requirements (minimum 5 criteria)
- **Definition of Done**: Clear completion checklist

Each description MUST contain at least 10 sentences total. Be thorough and professional.

Format as JSON array with objects containing "task_number" and "description" fields. Use JIRA markdown formatting."""

            description_response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=[{"role": "user", "content": bulk_prompt}],
                temperature=0.2,
                max_tokens=3000
            )
            
            # Parse the response to extract descriptions
            descriptions = {}
            try:
                import json
                response_data = json.loads(description_response.choices[0].message.content.strip())
                for item in response_data:
                    descriptions[item["task_number"]] = item["description"]
            except Exception:
                # Fallback: use detailed descriptions if JSON parsing fails
                for i, task in enumerate(tasks, 1):
                    descriptions[i] = f"""**Overview**: {task}. This task is essential for the overall project functionality and user experience. It requires careful implementation to ensure scalability and maintainability. The solution should follow best practices and coding standards.

**Background**: This feature is critical for meeting the project requirements and user expectations. It will integrate with existing system components and may affect other parts of the application. Proper implementation will enhance the overall system architecture.

**Implementation Details**: The development should use appropriate design patterns and follow the existing codebase structure. Consider performance implications and potential edge cases during implementation. Ensure proper error handling and logging are implemented throughout the solution.

**Acceptance Criteria**:
- Feature implementation is complete and functional
- All unit tests pass with minimum 80% code coverage
- Integration tests are written and passing
- Code follows project coding standards and guidelines
- Documentation is updated including API docs if applicable
- Performance requirements are met under expected load
- Security considerations are addressed appropriately

**Definition of Done**:
- Code is reviewed and approved by team lead
- All automated tests are passing
- Feature is deployed to staging environment
- QA testing is completed successfully"""
            
            # Create tickets with generated descriptions
            for i, task in enumerate(tasks, 1):
                try:
                    logger.info(f"Creating JIRA ticket for task: {task}")
                    
                    description = descriptions.get(i, f"Task: {task}")
                    metadata = f"\n\n---\n*Auto-generated by SprintAgent*\n*Created:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    final_description = description + metadata
                    
                    key = create_jira_ticket(task, final_description, state)
                    keys.append(key)
                    logger.info(f"Created ticket: {key}")
                    
                except Exception as e:
                    logger.error(f"Error creating ticket for task '{task}': {str(e)}")
                    keys.append(f"ERROR: {str(e)}")
            
            state["intermediate_result"] = keys
            state["agent_results"]["JiraAgent"] = keys
            state["agent_logs"].append(f"JiraAgent created {len(keys)} tickets with bulk-generated descriptions.")
            
    except Exception as e:
        logger.error(f"JiraAgent error: {e}")
        state["agent_logs"].append(f"JiraAgent error: {e}")
    
    # Move to next agent in queue
    state["__next__"] = state["agent_queue"].pop(0) if state["agent_queue"] else "END"
    return state

def git_agent_fn(state: AgentState) -> AgentState:
    """Get GitHub PR statuses."""
    try:
        keys = state.get("intermediate_result", [])
        results = []
        for key in keys:
            try:
                # Extract PR number from JIRA key (assuming format like PROJ-123)
                pr_number = int(key.split("-")[-1])
                status = get_pr_status(pr_number, state)
                results.append(status)
            except Exception as e:
                results.append({"error": str(e), "issue": key})
        
        state["intermediate_result"] = results
        state["agent_results"]["GitAgent"] = results
        state["agent_logs"].append(f"GitAgent checked {len(results)} PRs.")
        
    except Exception as e:
        logger.error(f"GitAgent error: {e}")
        state["agent_logs"].append(f"GitAgent error: {e}")
    
    # Move to next agent in queue
    state["__next__"] = state["agent_queue"].pop(0) if state["agent_queue"] else "END"
    return state

# === Sprint Assistant as AI Orchestrator ===
def sprint_agent_fn(state: AgentState) -> AgentState:
    """AI orchestrator that decides which agents to invoke."""
    try:
        client = get_openai_client()
        prompt = f"""You are SprintAssistant, an AI orchestrator for development workflow management.

Given the user input:
"{state['user_input']}"

Decide the intent and return the list of agents in the sequence they should be executed to fulfill the query.
Use only these agents: RequirementAgent, JiraAgent, GitAgent.

Examples:
- "Build a user login system" → "RequirementAgent,JiraAgent"
- "Check status of PROJ-123" → "JiraAgent"
- "What's the status of PR 456?" → "GitAgent"
- "Create tickets for mobile app features" → "RequirementAgent,JiraAgent"

Return the list as a comma-separated string like: RequirementAgent,JiraAgent"""

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        sequence = response.choices[0].message.content.strip().split(",")
        queue = [agent.strip() for agent in sequence if agent.strip()]
        
        logger.info(f"SprintAgent decided execution order: {', '.join(queue)}")
        
        # Set up the execution queue and initialize state
        state["agent_queue"] = queue
        state["agent_logs"] = [f"SprintAgent decided execution order: {', '.join(queue)}"]
        state["agent_results"] = {}
        state["intermediate_result"] = state["user_input"]
        
        # Set next agent to execute
        state["__next__"] = queue.pop(0) if queue else "END"
        
        return state
    except Exception as e:
        logger.error(f"SprintAgent error: {e}")
        state["agent_logs"] = [f"SprintAgent error: {e}"]
        state["__next__"] = "END"
        return state

# === Initialize LangGraph Workflow ===
def create_workflow():
    """Create and compile the LangGraph workflow with proper conditional edges."""
    builder = StateGraph(AgentState)
    
    # Add all nodes
    builder.add_node("SprintAgent", RunnableLambda(sprint_agent_fn))
    builder.add_node("RequirementAgent", RunnableLambda(requirement_agent_fn))
    builder.add_node("JiraAgent", RunnableLambda(jira_agent_fn))
    builder.add_node("GitAgent", RunnableLambda(git_agent_fn))
    
    # Set entry point
    builder.set_entry_point("SprintAgent")
    
    # Create branching logic based on __next__ field
    def route_next(state: AgentState) -> str:
        """Route to the next agent based on the __next__ field."""
        next_agent = state.get("__next__", "END")
        if next_agent in ["RequirementAgent", "JiraAgent", "GitAgent"]:
            return next_agent
        return END
    
    # Add conditional edges from each node
    builder.add_conditional_edges("SprintAgent", route_next)
    builder.add_conditional_edges("RequirementAgent", route_next)
    builder.add_conditional_edges("JiraAgent", route_next)
    builder.add_conditional_edges("GitAgent", route_next)
    
    return builder.compile()

# === Startup and Shutdown ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Sprint Agent API Server...")
    
    # Initialize JIRA handler if possible
    try:
        app_state["jira_handler"] = JiraHandler()
        logger.info("✅ JIRA Handler initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ JIRA Handler initialization failed: {e}")
        app_state["jira_handler"] = None
    
    # Initialize workflow
    app_state["workflow"] = create_workflow()
    logger.info("✅ LangGraph workflow initialized")
    
    # Test OpenAI connection
    try:
        get_openai_client()
        logger.info("✅ OpenAI client initialized")
    except Exception as e:
        logger.error(f"❌ OpenAI client initialization failed: {e}")
    
    logger.info("🎯 Sprint Agent API Server is ready!")
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Sprint Agent API Server...")

# === FastAPI App ===
app = FastAPI(
    title="Sprint Agent API",
    description="Multi-agent system for development workflow management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API Endpoints ===

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sprint Agent API Server",
        "version": "1.0.0",
        "description": "Multi-agent system for development workflow management",
        "endpoints": [
            "POST /process - Process natural language requirements",
            "GET /health - Check system health", 
            "GET /test - API testing interface",
            "GET /docs - API documentation"
        ]
    }

@app.get("/test", response_class=HTMLResponse)
async def test_interface():
    """Serve the API testing interface."""
    try:
        with open(os.path.join(os.path.dirname(__file__), "api_test_interface.html"), "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <body>
                    <h1>API Testing Interface Not Found</h1>
                    <p>The testing interface file is missing. Please ensure api_test_interface.html exists.</p>
                    <p><a href="/docs">Go to API Documentation</a></p>
                </body>
            </html>
            """,
            status_code=404
        )

@app.get("/health", response_model=HealthResponseModel)
async def health_check():
    """Health check endpoint."""
    components = {}
    
    # Check OpenAI
    try:
        get_openai_client()
        components["openai"] = "✅ OK"
    except Exception as e:
        components["openai"] = f"❌ FAILED: {str(e)}"
    
    # Check JIRA Handler
    if app_state["jira_handler"]:
        components["jira_handler"] = "✅ OK"
    else:
        components["jira_handler"] = "⚠️ Not initialized"
    
    # Check Workflow
    if app_state["workflow"]:
        components["langgraph_workflow"] = "✅ OK"
    else:
        components["langgraph_workflow"] = "❌ Not initialized"
    
    # Check environment variables
    env_vars = ["OPENAI_API_KEY", "JIRA_SERVER", "JIRA_USERNAME", "JIRA_API_TOKEN"]
    for var in env_vars:
        if os.getenv(var):
            components[f"env_{var.lower()}"] = "✅ Set"
        else:
            components[f"env_{var.lower()}"] = "⚠️ Not set"
    
    # Determine overall status
    failed_components = [k for k, v in components.items() if "❌" in v]
    if failed_components:
        status = "degraded"
        message = f"Some components failed: {', '.join(failed_components)}"
    else:
        status = "healthy"
        message = "All systems operational"
    
    return HealthResponseModel(
        status=status,
        message=message,
        components=components
    )

@app.post("/process", response_model=ProcessResponseModel)
async def process_requirement(request: ProcessRequestModel):
    """Process natural language requirement through the multi-agent system."""
    try:
        logger.info(f"📝 Processing request: {request.requirement[:100]}...")
        
        # Validate workflow is available
        if not app_state["workflow"]:
            raise HTTPException(status_code=500, detail="Workflow not initialized")
        
        # Use environment variables as defaults, allow override from request
        jira_domain = request.jira_server or os.getenv("JIRA_SERVER")
        jira_email = request.jira_username or os.getenv("JIRA_USERNAME")
        jira_token = request.jira_api_token or os.getenv("JIRA_API_TOKEN")
        jira_project = request.jira_project or os.getenv("JIRA_PROJECT_KEY", "TEST")
        github_token = request.github_token or os.getenv("GITHUB_TOKEN", "dummy_token")
        github_repo = request.github_repo or "owner/repo"
        
        # Validate required JIRA credentials
        if not all([jira_domain, jira_email, jira_token]):
            raise HTTPException(
                status_code=400, 
                detail="Missing JIRA credentials. Provide in request or set environment variables."
            )
        
        # Create initial state matching app 1.py structure
        initial_state: AgentState = {
            "user_input": request.requirement,
            "intermediate_result": "",
            "agent_queue": [],
            "agent_logs": [],
            "agent_results": {},
            "jira_email": jira_email,
            "jira_token": jira_token,
            "jira_domain": jira_domain,
            "jira_project": jira_project,
            "github_token": github_token,
            "github_repo": github_repo,
            "__next__": ""
        }
        
        # Process through workflow
        logger.info("🔄 Processing through LangGraph workflow...")
        result = app_state["workflow"].invoke(initial_state)
        
        # Format response based on agent results
        success = bool(result.get('agent_results'))
        
        # Extract results from different agents
        tasks = result.get('agent_results', {}).get('RequirementAgent', [])
        jira_keys = result.get('agent_results', {}).get('JiraAgent', [])
        pr_statuses = result.get('agent_results', {}).get('GitAgent', [])
        
        response_data = {
            "workflow_result": result,
            "agent_logs": result.get('agent_logs', []),
            "summary": {
                "tasks_generated": len(tasks) if tasks else 0,
                "tickets_created": len([k for k in jira_keys if not str(k).startswith('ERROR')]) if jira_keys else 0,
                "errors": len([k for k in jira_keys if str(k).startswith('ERROR')]) if jira_keys else 0,
                "pr_statuses_checked": len(pr_statuses) if pr_statuses else 0
            }
        }
        
        # Build response message from agent logs
        if result.get('agent_logs'):
            message = "; ".join(result['agent_logs'][-3:])  # Show last 3 log entries
        else:
            message = "Request processed"
        
        logger.info(f"✅ Processing completed: {message}")
        
        return ProcessResponseModel(
            success=success,
            message=message,
            data=response_data,
            tasks=tasks,
            jira_keys=jira_keys,
            pr_statuses=pr_statuses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/tickets")
async def get_all_tickets(project_key: Optional[str] = None, max_results: int = 50):
    """Get all tickets from JIRA project."""
    try:
        if not app_state["jira_handler"]:
            raise HTTPException(status_code=500, detail="JIRA handler not available")
        
        project_key = project_key or os.getenv("JIRA_PROJECT_KEY", "TEST")
        result = app_state["jira_handler"].get_all_tickets(project_key, max_results)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch tickets"))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tickets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {str(e)}")

@app.get("/tickets/{ticket_key}")
async def get_ticket_details(ticket_key: str):
    """Get detailed information about a specific ticket."""
    try:
        if not app_state["jira_handler"]:
            raise HTTPException(status_code=500, detail="JIRA handler not available")
        
        result = app_state["jira_handler"].get_ticket_by_id(ticket_key)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Ticket not found"))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket {ticket_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticket: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
