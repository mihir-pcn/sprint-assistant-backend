from jira import JIRA
from typing import List, Dict, Any, Optional
from .config import Config
from .models import (TicketInfo, TicketRequest, TicketComment, TicketPriority, TicketType, 
                   TicketUpdate, TicketHistory, TicketHistoryResponse)
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Constants
TIMEZONE_UTC = '+00:00'

class JiraClient:
    """JIRA API client wrapper"""
    
    def __init__(self):
        """Initialize JIRA client"""
        self.jira = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to JIRA"""
        try:
            options = {
                'server': Config.JIRA_SERVER
            }
            # Remove trailing slash if present
            if options['server'].endswith('/'):
                options['server'] = options['server'][:-1]
                
            self.jira = JIRA(
                options=options,
                basic_auth=(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
            )
            logger.info("Successfully connected to JIRA")
        except Exception as e:
            logger.error(f"Failed to connect to JIRA: {e}")
            raise
    
    def create_ticket(self, ticket: TicketRequest) -> str:
        """Create a new JIRA ticket"""
        try:
            # Build the issue dictionary
            issue_dict = {
                'project': {'key': ticket.project_key},
                'summary': ticket.summary,
                'description': ticket.description,
                'issuetype': {'name': ticket.issue_type.value},
            }
            
            # Add parent field for subtasks
            if ticket.issue_type == TicketType.SUBTASK and ticket.parent_key:
                issue_dict['parent'] = {'key': ticket.parent_key}
            
            # Only add priority if it's not None and not an Epic (Epics typically don't have priority)
            if ticket.priority and ticket.issue_type != TicketType.EPIC:
                issue_dict['priority'] = {'name': ticket.priority.value}
            
            # Add assignee if specified
            if ticket.assignee:
                issue_dict['assignee'] = {'name': ticket.assignee}
            
            # Add labels if specified
            if ticket.labels:
                issue_dict['labels'] = ticket.labels
            
            # Add components if specified
            if ticket.components:
                issue_dict['components'] = [{'name': comp} for comp in ticket.components]
            
            # Add story points if specified
            if ticket.story_points is not None:
                # Story Points field may be named differently in different JIRA instances
                # Common field names: customfield_10016, customfield_10002, customfield_10004
                try:
                    # First try to find the Story Points field
                    fields = self.jira.fields()
                    story_points_field = None
                    for field in fields:
                        if 'story' in field['name'].lower() and 'point' in field['name'].lower():
                            story_points_field = field['id']
                            break
                    
                    if story_points_field:
                        issue_dict[story_points_field] = ticket.story_points
                    else:
                        # Try common field IDs
                        issue_dict['customfield_10016'] = ticket.story_points
                except Exception as e:
                    logger.warning(f"Could not set story points: {e}")
            
            # Add dates if specified
            if ticket.start_date:
                try:
                    # Start Date is often a custom field
                    issue_dict['customfield_10015'] = ticket.start_date  # Common Start Date field
                except Exception as e:
                    logger.warning(f"Could not set start date: {e}")
            
            if ticket.due_date:
                try:
                    issue_dict['duedate'] = ticket.due_date
                except Exception as e:
                    logger.warning(f"Could not set due date: {e}")
            
            issue = self.jira.create_issue(fields=issue_dict)
            return issue.key
        except Exception as e:
            print(f"Error creating ticket: {str(e)}")
            raise
    
    def get_ticket(self, ticket_key: str) -> TicketInfo:
        """Get ticket information by key"""
        try:
            issue = self.jira.issue(ticket_key)
            
            # Extract assignee
            assignee = None
            if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                assignee = issue.fields.assignee.displayName
            
            # Extract labels
            labels = []
            if hasattr(issue.fields, 'labels') and issue.fields.labels:
                labels = issue.fields.labels
            
            # Extract components
            components = []
            if hasattr(issue.fields, 'components') and issue.fields.components:
                components = [comp.name for comp in issue.fields.components]
            
            # Extract story points
            story_points = None
            try:
                # Try common story points field names
                for field_name in ['customfield_10016', 'customfield_10002', 'customfield_10004']:
                    if hasattr(issue.fields, field_name):
                        field_value = getattr(issue.fields, field_name)
                        if field_value is not None:
                            story_points = int(field_value)
                            break
            except Exception as e:
                logger.debug(f"Could not extract story points: {e}")
            
            # Extract dates
            start_date = None
            due_date = None
            try:
                # Try common start date field
                if hasattr(issue.fields, 'customfield_10015') and issue.fields.customfield_10015:
                    start_date = str(issue.fields.customfield_10015)
                
                if hasattr(issue.fields, 'duedate') and issue.fields.duedate:
                    due_date = str(issue.fields.duedate)
            except Exception as e:
                logger.debug(f"Could not extract dates: {e}")
            
            # Calculate status duration
            status_duration = self._calculate_status_duration(issue)
            
            return TicketInfo(
                key=issue.key,
                summary=issue.fields.summary,
                description=issue.fields.description or "",
                status=issue.fields.status.name,
                priority=issue.fields.priority.name if issue.fields.priority else "Medium",
                issue_type=issue.fields.issuetype.name,
                assignee=assignee,
                reporter=issue.fields.reporter.displayName,
                created=datetime.fromisoformat(issue.fields.created.replace('Z', TIMEZONE_UTC)),
                updated=datetime.fromisoformat(issue.fields.updated.replace('Z', TIMEZONE_UTC)),
                labels=labels,
                components=components,
                story_points=story_points,
                start_date=start_date,
                due_date=due_date,
                status_duration=status_duration
            )
            
        except Exception as e:
            logger.error(f"Failed to get ticket {ticket_key}: {e}")
            raise
    
    def search_tickets(self, jql_query: str, max_results: int = 50) -> List[TicketInfo]:
        """Search for tickets using JQL"""
        try:
            issues = self.jira.search_issues(jql_query, maxResults=max_results)
            tickets = []
            
            for issue in issues:
                # Extract assignee
                assignee = None
                if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                    assignee = issue.fields.assignee.displayName
                
                # Extract labels
                labels = []
                if hasattr(issue.fields, 'labels') and issue.fields.labels:
                    labels = issue.fields.labels
                
                # Extract components
                components = []
                if hasattr(issue.fields, 'components') and issue.fields.components:
                    components = [comp.name for comp in issue.fields.components]
                
                ticket = TicketInfo(
                    key=issue.key,
                    summary=issue.fields.summary,
                    description=issue.fields.description or "",
                    status=issue.fields.status.name,
                    priority=issue.fields.priority.name if issue.fields.priority else "Medium",
                    issue_type=issue.fields.issuetype.name,
                    assignee=assignee,
                    reporter=issue.fields.reporter.displayName,
                    created=datetime.fromisoformat(issue.fields.created.replace('Z', TIMEZONE_UTC)),
                    updated=datetime.fromisoformat(issue.fields.updated.replace('Z', TIMEZONE_UTC)),
                    labels=labels,
                    components=components
                )
                tickets.append(ticket)
            
            return tickets
            
        except Exception as e:
            logger.error(f"Failed to search tickets: {e}")
            raise
    
    def add_comment(self, ticket_key: str, comment: str) -> None:
        """Add a comment to a ticket"""
        try:
            self.jira.add_comment(ticket_key, comment)
            logger.info(f"Added comment to {ticket_key}")
        except Exception as e:
            logger.error(f"Failed to add comment to {ticket_key}: {e}")
            raise
    
    def update_ticket_status(self, ticket_key: str, status: str) -> None:
        """Update ticket status"""
        try:
            # Get available transitions
            transitions = self.jira.transitions(ticket_key)
            
            # Find the transition that matches the desired status
            transition_id = None
            for transition in transitions:
                if transition['to']['name'].lower() == status.lower():
                    transition_id = transition['id']
                    break
            
            if transition_id:
                self.jira.transition_issue(ticket_key, transition_id)
                logger.info(f"Updated {ticket_key} status to {status}")
            else:
                available_statuses = [t['to']['name'] for t in transitions]
                raise ValueError(f"Status '{status}' not available. Available: {available_statuses}")
                
        except Exception as e:
            logger.error(f"Failed to update status for {ticket_key}: {e}")
            raise
    
    def assign_ticket(self, ticket_key: str, assignee: str) -> None:
        """Assign a ticket to a user"""
        try:
            # Handle special cases
            if not assignee or assignee.lower() in ['unassigned', 'none', 'null', '']:
                # Unassign the ticket
                self.jira.assign_issue(ticket_key, None)
                logger.info(f"Unassigned {ticket_key}")
            else:
                # Assign to specific user
                self.jira.assign_issue(ticket_key, assignee)
                logger.info(f"Assigned {ticket_key} to {assignee}")
                
        except Exception as e:
            logger.error(f"Failed to assign {ticket_key} to {assignee}: {e}")
            raise
    
    def get_ticket_comments(self, ticket_key: str) -> List[TicketComment]:
        """Get all comments for a ticket"""
        try:
            issue = self.jira.issue(ticket_key, expand='comments')
            comments = []
            
            for comment in issue.fields.comment.comments:
                ticket_comment = TicketComment(
                    body=comment.body,
                    author=comment.author.displayName,
                    created=datetime.fromisoformat(comment.created.replace('Z', TIMEZONE_UTC))
                )
                comments.append(ticket_comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Failed to get comments for {ticket_key}: {e}")
            raise
    
    def get_projects(self) -> List[Dict[str, str]]:
        """Get all available projects"""
        try:
            projects = self.jira.projects()
            return [{'key': p.key, 'name': p.name} for p in projects]
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise

    def update_ticket(self, update: TicketUpdate) -> bool:
        """Update a JIRA ticket with new values"""
        try:
            issue = self.jira.issue(update.ticket_key)
            update_dict = {}
            
            # Update status
            if update.status:
                try:
                    self.jira.transition_issue(issue, update.status)
                except Exception as e:
                    logger.warning(f"Could not transition to status {update.status}: {e}")
            
            # Update priority
            if update.priority:
                update_dict['priority'] = {'name': update.priority.value}
            
            # Update assignee
            if update.assignee is not None:
                if update.assignee == '':
                    update_dict['assignee'] = None  # Unassign
                else:
                    update_dict['assignee'] = {'name': update.assignee}
            
            # Update description
            if update.description:
                update_dict['description'] = update.description
            
            # Update labels
            if update.labels is not None:
                update_dict['labels'] = update.labels
            
            # Update story points
            if update.story_points is not None:
                # Try common story points field names
                for field_name in ['customfield_10016', 'customfield_10002', 'customfield_10004']:
                    try:
                        update_dict[field_name] = update.story_points
                        break
                    except:
                        continue
            
            # Update dates
            if update.start_date:
                update_dict['customfield_10015'] = update.start_date
            
            if update.due_date:
                update_dict['duedate'] = update.due_date
            
            # Apply updates
            if update_dict:
                issue.update(fields=update_dict)
            
            # Add comment if specified
            if update.comment:
                self.add_comment(update.ticket_key, update.comment)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update ticket {update.ticket_key}: {e}")
            raise

    def get_ticket_history(self, ticket_key: str) -> TicketHistoryResponse:
        """Get the change history of a ticket"""
        try:
            issue = self.jira.issue(ticket_key, expand='changelog')
            history_entries = []
            
            current_status = issue.fields.status.name
            status_duration = self._calculate_status_duration(issue)
            
            for changelog in issue.changelog.histories:
                for item in changelog.items:
                    history_entry = TicketHistory(
                        created=datetime.fromisoformat(changelog.created.replace('Z', TIMEZONE_UTC)),
                        author=changelog.author.displayName,
                        field=item.field,
                        from_value=item.fromString,
                        to_value=item.toString
                    )
                    history_entries.append(history_entry)
            
            # Sort by creation date
            history_entries.sort(key=lambda x: x.created)
            
            return TicketHistoryResponse(
                ticket_key=ticket_key,
                history=history_entries,
                current_status=current_status,
                status_duration=status_duration
            )
            
        except Exception as e:
            logger.error(f"Failed to get history for {ticket_key}: {e}")
            raise

    def _calculate_status_duration(self, issue) -> str:
        """Calculate how long a ticket has been in its current status"""
        try:
            current_status = issue.fields.status.name
            now = datetime.now(timezone.utc)
            
            # Get the last status change from changelog
            last_status_change = None
            
            if hasattr(issue, 'changelog') and issue.changelog:
                for changelog in reversed(issue.changelog.histories):
                    for item in changelog.items:
                        if item.field == 'status':
                            last_status_change = datetime.fromisoformat(changelog.created.replace('Z', TIMEZONE_UTC))
                            break
                    if last_status_change:
                        break
            
            # If no status change found, use creation date
            if not last_status_change:
                last_status_change = datetime.fromisoformat(issue.fields.created.replace('Z', TIMEZONE_UTC))
            
            # Calculate duration
            duration = now - last_status_change.replace(tzinfo=timezone.utc)
            
            # Format duration
            days = duration.days
            hours = duration.seconds // 3600
            
            if days > 0:
                return f"{days} days, {hours} hours"
            elif hours > 0:
                return f"{hours} hours"
            else:
                minutes = duration.seconds // 60
                return f"{minutes} minutes"
                
        except Exception as e:
            logger.warning(f"Could not calculate status duration: {e}")
            return "Unknown"
