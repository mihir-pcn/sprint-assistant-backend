from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class TicketPriority(str, Enum):
    """JIRA ticket priority levels"""
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"

class TicketType(str, Enum):
    """Supported JIRA ticket types"""
    TASK = "Task"
    BUG = "Bug"
    STORY = "Story"
    EPIC = "Epic"
    SUBTASK = "Subtask"
    # Common Atlassian template types
    IMPROVEMENT = "Improvement" 
    NEW_FEATURE = "New Feature"

class TicketStatus(str, Enum):
    """Common JIRA ticket statuses"""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    BACKLOG = "Backlog"
    REVIEW = "In Review"

class TicketRequest(BaseModel):
    """Model for creating a new JIRA ticket"""
    summary: str = Field(..., description="Brief summary of the ticket")
    description: str = Field(..., description="Detailed description of the ticket")
    project_key: str = Field(..., description="JIRA project key")
    issue_type: TicketType = Field(default=TicketType.TASK, description="Type of the ticket")
    priority: Optional[TicketPriority] = Field(default=TicketPriority.MEDIUM, description="Priority level")
    assignee: Optional[str] = Field(None, description="Username of assignee")
    labels: List[str] = Field(default_factory=list, description="List of labels")
    components: List[str] = Field(default_factory=list, description="List of components")
    parent_key: Optional[str] = Field(None, description="Parent ticket key for subtasks")
    story_points: Optional[int] = Field(None, description="Story points for the ticket")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    
class TicketInfo(BaseModel):
    """Model for JIRA ticket information"""
    key: str
    summary: str
    description: Optional[str]
    status: str
    priority: str
    issue_type: str
    assignee: Optional[str]
    reporter: str
    created: datetime
    updated: datetime
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    story_points: Optional[int] = Field(None, description="Story points assigned to ticket")
    start_date: Optional[str] = Field(None, description="Start date of the ticket")
    due_date: Optional[str] = Field(None, description="Due date of the ticket")
    status_duration: Optional[str] = Field(None, description="How long ticket has been in current status")
    
class SearchQuery(BaseModel):
    """Model for searching JIRA tickets"""
    query: str = Field(..., description="Natural language search query")
    project_key: Optional[str] = Field(None, description="Limit search to specific project")
    status: Optional[List[str]] = Field(None, description="Filter by status")
    issue_type: Optional[List[str]] = Field(None, description="Filter by issue type")
    assignee: Optional[str] = Field(None, description="Filter by assignee")
    priority: Optional[List[str]] = Field(None, description="Filter by priority")
    max_results: int = Field(default=50, description="Maximum number of results")

class AIProcessingRequest(BaseModel):
    """Model for AI processing requests"""
    prompt: str = Field(..., description="User's natural language prompt")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for processing")
    
class ComplexTicketRequest(BaseModel):
    """Model for creating multiple related tickets (parent with subtasks)"""
    parent_ticket: TicketRequest = Field(..., description="Main parent ticket to create")
    subtasks: List[TicketRequest] = Field(default_factory=list, description="List of subtasks to create under the parent")

class AIProcessingResponse(BaseModel):
    """Response from AI processing of natural language prompt"""
    action: str = Field(..., description="Action to take: create, read, update, create_complex")
    explanation: str = Field(..., description="Explanation of what will be done")
    confidence: float = Field(..., description="Confidence level (0.0-1.0)")
    ticket_request: Optional[TicketRequest] = Field(None, description="For create actions")
    complex_ticket_request: Optional[ComplexTicketRequest] = Field(None, description="For create_complex actions")
    search_query: Optional[SearchQuery] = Field(None, description="For read actions")
    update_info: Optional[Dict[str, Any]] = Field(None, description="For update actions")

class TicketComment(BaseModel):
    """Model for ticket comments"""
    body: str = Field(..., description="Comment text")
    author: Optional[str] = Field(None, description="Comment author")
    created: Optional[datetime] = Field(None, description="Comment creation time")

class TicketUpdate(BaseModel):
    """Model for updating tickets"""
    ticket_key: str = Field(..., description="JIRA ticket key")
    status: Optional[str] = Field(None, description="New status")
    assignee: Optional[str] = Field(None, description="New assignee")
    priority: Optional[TicketPriority] = Field(None, description="New priority")
    comment: Optional[str] = Field(None, description="Comment to add")
    labels: Optional[List[str]] = Field(None, description="Labels to add/update")
    story_points: Optional[int] = Field(None, description="Story points to set")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    description: Optional[str] = Field(None, description="New description for the ticket")

class TicketHistory(BaseModel):
    """Model for ticket history entry"""
    created: datetime = Field(..., description="When the change was made")
    author: str = Field(..., description="Who made the change")
    field: str = Field(..., description="Field that was changed")
    from_value: Optional[str] = Field(None, description="Previous value")
    to_value: Optional[str] = Field(None, description="New value")

class TicketHistoryResponse(BaseModel):
    """Model for ticket history response"""
    ticket_key: str = Field(..., description="JIRA ticket key")
    history: List[TicketHistory] = Field(default_factory=list, description="List of history entries")
    current_status: str = Field(..., description="Current status of the ticket")
    status_duration: str = Field(..., description="How long the ticket has been in current status")
