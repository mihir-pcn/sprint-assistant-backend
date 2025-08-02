from .jira_client import JiraClient
from .models import (TicketInfo, TicketRequest, SearchQuery, 
                   ComplexTicketRequest, TicketType, TicketUpdate, TicketPriority)
from .config import Config
from typing import List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class JiraAgent:
    """Main JIRA AI Agent class that orchestrates all operations"""
    
    def __init__(self):
        """Initialize the JIRA AI agent"""
        if not Config.validate():
            raise ValueError("Invalid configuration. Please check your environment variables.")
        
        self.jira_client = JiraClient()
        
        # Context memory for ticket operations
        self.current_ticket_context = None
        self.context_history = []
        
        # Get available projects for context
        try:
            self.projects = self.jira_client.get_projects()
            logger.info(f"Loaded {len(self.projects)} projects")
        except Exception as e:
            logger.warning(f"Could not load projects: {e}")
            self.projects = []
    
    def _extract_ticket_key(self, text: str) -> Optional[str]:
        """Extract ticket key from text"""
        words = text.upper().split()
        for word in words:
            if '-' in word and any(char.isdigit() for char in word):
                # Clean the ticket key by removing trailing punctuation
                return word.rstrip('.,;:!')
        return None
    
    def _update_ticket_context(self, ticket_key: str):
        """Update the current ticket context"""
        if self.current_ticket_context != ticket_key:
            # Add previous context to history if it exists
            if self.current_ticket_context:
                self.context_history.append(self.current_ticket_context)
                # Keep only last 5 contexts
                if len(self.context_history) > 5:
                    self.context_history.pop(0)
            
            self.current_ticket_context = ticket_key
            logger.info(f"Updated ticket context to {ticket_key}")
    
    def get_current_context(self) -> Optional[str]:
        """Get the current ticket context"""
        return self.current_ticket_context
    
    def clear_context(self):
        """Clear the current context"""
        if self.current_ticket_context:
            self.context_history.append(self.current_ticket_context)
            self.current_ticket_context = None
            logger.info("Cleared ticket context")
    
    def _handle_create_action(self, ticket_request: TicketRequest) -> dict:
        """Handle ticket creation"""
        try:
            # Validate project key
            if not ticket_request.project_key:
                if Config.JIRA_PROJECT_KEY:
                    ticket_request.project_key = Config.JIRA_PROJECT_KEY
                else:
                    return {'success': False, 'error': 'No project key specified and no default configured'}
            
            # Create the ticket
            ticket_key = self.jira_client.create_ticket(ticket_request)
            
            # Get the created ticket details
            ticket_info = self.jira_client.get_ticket(ticket_key)
            
            return {
                'success': True,
                'data': {
                    'ticket_key': ticket_key,
                    'issue_type': ticket_info.issue_type,
                    'priority': ticket_info.priority,
                    'ticket_info': ticket_info.dict(),
                    'message': f'Successfully created {ticket_info.issue_type} ticket {ticket_key}'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            return {'success': False, 'error': f'Failed to create ticket: {str(e)}'}
    
    def _handle_create_complex_action(self, complex_request: ComplexTicketRequest) -> dict:
        """Handle complex ticket creation (parent with subtasks)"""
        try:
            created_tickets = []
            
            # Validate project key for parent ticket
            if not complex_request.parent_ticket.project_key:
                if Config.JIRA_PROJECT_KEY:
                    complex_request.parent_ticket.project_key = Config.JIRA_PROJECT_KEY
                else:
                    return {'error': 'No project key specified and no default configured'}
            
            # Create parent ticket
            parent_key = self.jira_client.create_ticket(complex_request.parent_ticket)
            parent_info = self.jira_client.get_ticket(parent_key)
            
            created_tickets.append({
                'key': parent_key,
                'type': 'parent',
                'issue_type': parent_info.issue_type,
                'summary': parent_info.summary
            })
            
            # Create subtasks
            for subtask_request in complex_request.subtasks:
                try:
                    # Set parent key and project key for subtask
                    subtask_request.parent_key = parent_key
                    subtask_request.project_key = complex_request.parent_ticket.project_key
                    subtask_request.issue_type = TicketType.SUBTASK
                    
                    subtask_key = self.jira_client.create_ticket(subtask_request)
                    subtask_info = self.jira_client.get_ticket(subtask_key)
                    
                    created_tickets.append({
                        'key': subtask_key,
                        'type': 'subtask',
                        'issue_type': subtask_info.issue_type,
                        'summary': subtask_info.summary,
                        'parent': parent_key
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to create subtask: {e}")
                    created_tickets.append({
                        'error': f'Failed to create subtask: {str(e)}',
                        'summary': subtask_request.summary
                    })
            
            return {
                'success': True,
                'data': {
                    'parent_key': parent_key,
                    'created_tickets': created_tickets,
                    'message': f'Successfully created {len(created_tickets)} tickets with parent {parent_key}'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create complex ticket structure: {e}")
            return {'error': f'Failed to create complex ticket structure: {str(e)}'}
    
    def _handle_show_ticket_action(self, ticket_key: str) -> dict:
        """Handle showing ticket details"""
        try:
            ticket_info = self.jira_client.get_ticket(ticket_key)
            
            # Update context with this ticket
            self._update_ticket_context(ticket_key)
            
            return {
                'success': True,
                'action': 'show_ticket',
                'data': {
                    'ticket_key': ticket_key,
                    'ticket_info': ticket_info.dict()
                },
                'explanation': f'Retrieved details for ticket {ticket_key}',
                'confidence': 1.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticket {ticket_key}: {e}")
            return {
                'success': False,
                'error': f'Failed to get ticket {ticket_key}: {str(e)}'
            }
    
    def search_tickets(self, query: SearchQuery) -> dict:
        """Search for tickets"""
        try:
            tickets = self.jira_client.search_tickets(query)
            
            return {
                'success': True,
                'data': {
                    'tickets': [ticket.dict() for ticket in tickets],
                    'count': len(tickets)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search tickets: {e}")
            return {
                'success': False,
                'error': f'Failed to search tickets: {str(e)}'
            }
    
    def get_ticket(self, ticket_key: str) -> TicketInfo:
        """Get ticket details directly"""
        return self.jira_client.get_ticket(ticket_key)
    
    def update_ticket(self, ticket_key: str, update: TicketUpdate) -> bool:
        """Update ticket directly"""
        return self.jira_client.update_ticket(ticket_key, update)
    
    def create_ticket_direct(self, summary: str, description: str, 
                            issue_type: TicketType = TicketType.TASK,
                            priority: TicketPriority = TicketPriority.MEDIUM,
                            assignee: str = None,
                            project_key: str = None) -> str:
        """Create a ticket directly with parameters"""
        
        if not project_key:
            project_key = Config.JIRA_PROJECT_KEY
            
        ticket_request = TicketRequest(
            summary=summary,
            description=description,
            project_key=project_key,
            issue_type=issue_type,
            priority=priority,
            assignee=assignee
        )
        
        try:
            return self.jira_client.create_ticket(ticket_request)
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            raise
