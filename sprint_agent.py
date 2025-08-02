import streamlit as st
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from jira import JIRA
from github import Github
from openai import OpenAI
from langchain_core.runnables import RunnableLambda
import os
import sys

# Add jira_agent to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'jira_agent'))

# Try to load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, skip
    pass
 
# === LangGraph Agent State ===
class AgentState(TypedDict):
    input: str
    tasks: List[str]
    jira_keys: List[str]
    pr_statuses: List[dict]
    jira_domain: str
    jira_email: str
    jira_token: str
    jira_project: str
    github_token: str
    github_repo: str
    __next__: str
 
# === OpenAI Client ===
def get_openai_client():
    # First try environment variable
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # If not found, try session state (from sidebar input)
    if not openai_api_key and hasattr(st.session_state, 'openai_api_key'):
        openai_api_key = st.session_state.openai_api_key
    
    if not openai_api_key:
        st.error("⚠️ OpenAI API key not found!")
        st.info("Please either:")
        st.info("1. Set the OPENAI_API_KEY environment variable, or")
        st.info("2. Enter your API key in the sidebar")
        st.info("Get an API key from: https://platform.openai.com/api-keys")
        st.stop()
    
    return OpenAI(api_key=openai_api_key)
 
# === JIRA + GitHub Functions ===
def create_jira_ticket(summary, description, state: AgentState):
    try:
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
        st.error(f"Error creating JIRA ticket: {str(e)}")
        return f"ERROR: {str(e)}"
 
def get_pr_status(pr_number: int, state: AgentState):
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
    try:
        client = get_openai_client()
        prompt = f"Convert the following requirement into a list of development tasks:\n\n{state['input']}\n\nReturn as a numbered list."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip().split("\n")
        tasks = [line.strip("\u2022-* ").strip() for line in raw if line.strip() and any(c.isalpha() for c in line)]
        return {**state, "tasks": tasks}
    except Exception as e:
        st.error(f"Error in requirement agent: {str(e)}")
        return {**state, "tasks": []}
 
def jira_agent_fn(state: AgentState) -> AgentState:
    if not state["tasks"]:
        return state  # No tasks to create tickets for
    
    keys = []
    for task in state['tasks']:
        try:
            key = create_jira_ticket(task, "Auto-created by SprintAgent", state)
            keys.append(key)
        except Exception as e:
            st.error(f"Error creating ticket for task '{task}': {str(e)}")
            keys.append(f"ERROR: {str(e)}")
    
    return {**state, "jira_keys": keys}
 
def git_agent_fn(state: AgentState) -> AgentState:
    results = []
    for key in state['jira_keys']:
        try:
            # Extract PR number from JIRA key (assuming format like PROJ-123)
            pr_number = int(key.split("-")[-1])
            status = get_pr_status(pr_number, state)
            results.append(status)
        except Exception as e:
            results.append({"error": str(e), "issue": key})
    return {**state, "pr_statuses": results}
 
# === Sprint Assistant as AI Orchestrator ===
def sprint_agent_fn(state: AgentState) -> AgentState:
    try:
        client = get_openai_client()
        prompt = f"""
You are SprintAssistant. Given the user input:
"{state['input']}"
Decide the intent:
1. If the user wants to create tasks/tickets from a requirement → return "RequirementAgent"
2. If the user wants Jira ticket info or status → return "JiraAgent"  
3. If the user wants PR status or GitHub info → return "GitAgent"
Respond with only one agent name from the above.
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        next_agent = response.choices[0].message.content.strip()
 
        if next_agent == "RequirementAgent":
            state = requirement_agent_fn(state)
            state = jira_agent_fn(state)
        elif next_agent == "JiraAgent":
            state = jira_agent_fn(state)
        elif next_agent == "GitAgent":
            state = git_agent_fn(state)
 
        return {**state, "__next__": "END"}
    except Exception as e:
        st.error(f"Error in sprint agent: {str(e)}")
        return {**state, "__next__": "END"}
 
# === LangGraph ===
builder = StateGraph(AgentState)
builder.add_node("SprintAgent", RunnableLambda(sprint_agent_fn))
builder.set_entry_point("SprintAgent")
builder.add_edge("SprintAgent", END)
workflow = builder.compile()
 
# === Streamlit UI ===
st.set_page_config(page_title="LangGraph Sprint Assistant", layout="centered")
st.title("🤖 SprintAgent with LangGraph")
 
st.sidebar.subheader("🔐 Project Manager Login")
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# OpenAI API Key input
st.sidebar.subheader("🤖 OpenAI Configuration")
if not os.getenv("OPENAI_API_KEY"):
    api_key_input = st.sidebar.text_input(
        "OpenAI API Key", 
        type="password", 
        help="Enter your OpenAI API key or set OPENAI_API_KEY environment variable"
    )
    if api_key_input:
        st.session_state.openai_api_key = api_key_input
        st.sidebar.success("✅ API Key provided")
    else:
        st.sidebar.warning("⚠️ OpenAI API Key required")
else:
    st.sidebar.success("✅ OpenAI API Key found in environment")
 
# Authentication and configuration
if not st.session_state.authenticated:
    st.sidebar.subheader("🔧 Configuration")
    
    # Use environment variables as defaults
    default_jira_email = os.getenv("JIRA_USERNAME", "")
    default_jira_domain = os.getenv("JIRA_SERVER", "")
    default_jira_project = os.getenv("JIRA_PROJECT_KEY", "TEST")
    
    jira_email = st.sidebar.text_input("Jira Email", value=default_jira_email)
    jira_token = st.sidebar.text_input("Jira API Token", type="password", 
                                     value=os.getenv("JIRA_API_TOKEN", ""))
    jira_domain = st.sidebar.text_input("Jira Domain", value=default_jira_domain)
    jira_project = st.sidebar.text_input("Jira Project Key", value=default_jira_project)
    github_token = st.sidebar.text_input("GitHub Token", type="password")
    github_repo = st.sidebar.text_input("GitHub Repo (owner/repo)", value="owner/repo")
    
    if st.sidebar.button("🔓 Login with Jira & GitHub"):
        if jira_email and jira_token and jira_domain and jira_project:
            st.session_state.authenticated = True
            st.session_state.jira_email = jira_email
            st.session_state.jira_token = jira_token
            st.session_state.jira_domain = jira_domain
            st.session_state.jira_project = jira_project
            st.session_state.github_token = github_token or "dummy_token"
            st.session_state.github_repo = github_repo
            st.rerun()
        else:
            st.sidebar.error("Please fill in all required JIRA fields")
    
    st.sidebar.info("Please configure and login to access SprintAgent.")
    st.stop()
 
st.sidebar.success("✅ Logged in")
st.sidebar.text(f"Jira Email: {st.session_state.jira_email}")
st.sidebar.text(f"Jira Project: {st.session_state.jira_project}")
st.sidebar.text(f"GitHub Repo: {st.session_state.github_repo}")

# Add logout button
if st.sidebar.button("🔓 Logout"):
    st.session_state.authenticated = False
    st.rerun()
 
if "messages" not in st.session_state:
    st.session_state.messages = []
 
# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
 
user_input = st.chat_input("Describe a feature, ask to create Jira tickets, or check PR status")
 
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
 
    # Create initial state
    initial_state: AgentState = {
        "input": user_input,
        "tasks": [],
        "jira_keys": [],
        "pr_statuses": [],
        "jira_email": st.session_state.jira_email,
        "jira_token": st.session_state.jira_token,
        "jira_domain": st.session_state.jira_domain,
        "jira_project": st.session_state.jira_project,
        "github_token": st.session_state.github_token,
        "github_repo": st.session_state.github_repo,
        "__next__": ""
    }
 
    # Process with workflow
    with st.spinner("Processing your request..."):
        result = workflow.invoke(initial_state)
 
    # Format response
    response = ""
    if result['tasks']:
        response += "\n### Tasks Generated:\n- " + "\n- ".join(result['tasks'])
    if result['jira_keys']:
        response += "\n\n### Jira Tickets:\n- " + "\n- ".join(result['jira_keys'])
    if result['pr_statuses']:
        response += "\n\n### PR Statuses:\n"
        for status in result['pr_statuses']:
            if 'error' in status:
                response += f"- Error: {status['error']} (Issue: {status.get('issue', status.get('pr_number', 'Unknown'))})\n"
            else:
                response += f"- {status['title']} → {status['state']}, merged={status['merged']} ([Link]({status['url']}))\n"
 
    # Display response
    with st.chat_message("assistant"):
        st.markdown(response if response.strip() else "I couldn't process your request. Please try again or check your configuration.")
    st.session_state.messages.append({"role": "assistant", "content": response if response.strip() else "I couldn't process your request. Please try again or check your configuration."})