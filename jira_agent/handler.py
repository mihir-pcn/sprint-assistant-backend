#!/usr/bin/env python3
"""
JIRA AI Agent - Handler Module

Simple handler interface for processing JSON requirements and creating JIRA tickets.
This module provides a direct interface to the JSON processing functionality without
requiring the API server.
"""

import logging
import json
from typing import Dict, Any, Union
from .json_processor import JSONProcessor
from .jira_agent import JiraAgent
from .config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class JiraHandler:
    """
    Main handler class for processing JSON requirements and creating JIRA tickets.
    Provides a simple interface that combines JSON processing and JIRA operations.
    """
    
    def __init__(self):
        """Initialize the handler with required components"""
        try:
            # Validate configuration
            if not Config.validate():
                raise ValueError("Invalid configuration. Please check your environment variables.")
            
            # Initialize components
            self.json_processor = JSONProcessor()
            self.jira_agent = JiraAgent()
            
            logger.info("✅ JIRA Handler initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize JIRA Handler: {e}")
            raise
    
    def process_json_requirements(self, json_data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Main function to process JSON requirements and create JIRA tickets.
        
        Args:
            json_data: Either a dictionary containing the JSON data or a JSON string
            
        Returns:
            Dictionary containing the processing results with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "created_tickets": [...],
                    "summary": {...},
                    "source_info": {...}
                },
                "error": str (only if success is False)
            }
        """
        try:
            # Handle string input (parse JSON)
            if isinstance(json_data, str):
                try:
                    json_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Invalid JSON string: {str(e)}",
                        "message": "❌ Failed to parse JSON input"
                    }
            
            # Validate input
            if not isinstance(json_data, dict):
                return {
                    "success": False,
                    "error": "Input must be a dictionary or valid JSON string",
                    "message": "❌ Invalid input format"
                }
            
            logger.info(f"🧠 Processing JSON requirements: {json_data.get('title', 'Unknown')}")
            
            # Step 1: Process JSON data using JSON processor
            processor_result = self.json_processor.process_json_input(json_data)
            
            if not processor_result.get('success'):
                return {
                    "success": False,
                    "error": processor_result.get('error', 'JSON processing failed'),
                    "message": f"❌ Error: {processor_result.get('error', 'JSON processing failed')}"
                }
            
            # Step 2: Create tickets using the JIRA agent
            ticket_requests = processor_result['data']['ticket_requests']
            created_tickets = []
            
            logger.info(f"📋 Creating {len(ticket_requests)} JIRA tickets...")
            
            for i, ticket_request in enumerate(ticket_requests, 1):
                try:
                    logger.info(f"Creating ticket {i}/{len(ticket_requests)}: {ticket_request.summary}")
                    
                    # Use the agent to create the ticket
                    create_result = self.jira_agent._handle_create_action(ticket_request)
                    
                    if create_result.get('success'):
                        created_tickets.append({
                            'success': True,
                            'ticket_key': create_result.get('data', {}).get('ticket_key'),
                            'summary': ticket_request.summary,
                            'type': ticket_request.issue_type.value,
                            'assignee': ticket_request.assignee,
                            'priority': ticket_request.priority.value if ticket_request.priority else None
                        })
                        logger.info(f"✅ Created: {create_result.get('data', {}).get('ticket_key')}")
                    else:
                        created_tickets.append({
                            'success': False,
                            'error': create_result.get('error', 'Unknown error'),
                            'summary': ticket_request.summary,
                            'type': ticket_request.issue_type.value
                        })
                        logger.error(f"❌ Failed to create: {ticket_request.summary}")
                        
                except Exception as e:
                    logger.error(f"❌ Exception creating ticket '{ticket_request.summary}': {e}")
                    created_tickets.append({
                        'success': False,
                        'error': str(e),
                        'summary': ticket_request.summary,
                        'type': ticket_request.issue_type.value
                    })
            
            # Step 3: Format response
            successful_tickets = [t for t in created_tickets if t['success']]
            failed_tickets = [t for t in created_tickets if not t['success']]
            
            # Build response message
            message = f"✅ Processed JSON requirements and created {len(successful_tickets)} of {len(created_tickets)} tickets\n\n"
            
            if successful_tickets:
                message += "📋 Successfully Created:\n"
                for ticket in successful_tickets:
                    message += f"• {ticket['ticket_key']}: {ticket['summary']} ({ticket['type']})\n"
                message += "\n"
            
            if failed_tickets:
                message += "❌ Failed to Create:\n"
                for ticket in failed_tickets:
                    message += f"• {ticket['summary']} ({ticket['type']}): {ticket['error']}\n"
                message += "\n"
            
            # Add source information
            source_data = processor_result['data']['source_data']
            message += f"📊 Source: {source_data['title']}\n"
            message += f"🎯 Priority: {source_data['priority']}\n"
            message += f"👤 Assignee: {source_data['assignee'].get('dev', 'Not specified')}"
            
            # Prepare response data
            response_data = {
                'created_tickets': created_tickets,
                'summary': {
                    'total_requested': len(ticket_requests),
                    'successfully_created': len(successful_tickets),
                    'failed': len(failed_tickets)
                },
                'source_info': source_data,
                'processor_result': processor_result['data']  # Include original processor result
            }
            
            logger.info(f"🎉 Completed: {len(successful_tickets)}/{len(ticket_requests)} tickets created successfully")
            
            return {
                "success": len(successful_tickets) > 0,
                "message": message,
                "data": response_data
            }
            
        except Exception as e:
            error_msg = f"Failed to process JSON requirements: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "message": f"❌ Error: {error_msg}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the handler and its components.
        
        Returns:
            Dictionary with status information
        """
        try:
            return {
                "handler_status": "ready",
                "jira_connection": "connected" if self.jira_agent.jira_client else "disconnected",
                "projects_loaded": len(self.jira_agent.projects) if hasattr(self.jira_agent, 'projects') else 0,
                "current_context": self.jira_agent.get_current_context(),
                "config_valid": Config.validate()
            }
        except Exception as e:
            return {
                "handler_status": "error",
                "error": str(e)
            }
    
    def get_all_tickets(self, project_key: str = None, max_results: int = 50) -> Dict[str, Any]:
        """
        Get all tickets from JIRA with basic information.
        
        Args:
            project_key: Optional project key to filter tickets (uses default if not provided)
            max_results: Maximum number of tickets to return (default: 50)
            
        Returns:
            Dictionary containing list of tickets with basic information
        """
        try:
            if not project_key:
                project_key = Config.JIRA_PROJECT_KEY
            
            logger.info(f"🔍 Fetching all tickets from project: {project_key}")
            
            # Use JQL to search for tickets
            jql = f"project = {project_key} ORDER BY created DESC"
            
            # Get tickets using the JIRA client
            jira_client = self.jira_agent.jira_client.jira
            issues = jira_client.search_issues(jql, maxResults=max_results, expand='changelog')
            
            tickets = []
            for issue in issues:
                ticket_info = {
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'issue_type': issue.fields.issuetype.name,
                    'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                    'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'assignee_email': issue.fields.assignee.emailAddress if issue.fields.assignee else None,
                    'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                    'created': issue.fields.created,
                    'updated': issue.fields.updated,
                    'description': issue.fields.description[:200] + '...' if issue.fields.description and len(issue.fields.description) > 200 else issue.fields.description,
                    'labels': list(issue.fields.labels) if issue.fields.labels else [],
                    'components': [comp.name for comp in issue.fields.components] if issue.fields.components else [],
                    'fix_versions': [version.name for version in issue.fields.fixVersions] if issue.fields.fixVersions else []
                }
                
                # Add story points if available
                if hasattr(issue.fields, 'customfield_10016') and issue.fields.customfield_10016:
                    ticket_info['story_points'] = issue.fields.customfield_10016
                
                # Add epic link if available
                if hasattr(issue.fields, 'customfield_10014') and issue.fields.customfield_10014:
                    ticket_info['epic_link'] = issue.fields.customfield_10014
                
                # Add parent for subtasks
                if hasattr(issue.fields, 'parent') and issue.fields.parent:
                    ticket_info['parent'] = {
                        'key': issue.fields.parent.key,
                        'summary': issue.fields.parent.fields.summary
                    }
                
                tickets.append(ticket_info)
            
            logger.info(f"✅ Found {len(tickets)} tickets in project {project_key}")
            
            return {
                "success": True,
                "message": f"Found {len(tickets)} tickets in project {project_key}",
                "data": {
                    "tickets": tickets,
                    "project_key": project_key,
                    "total_count": len(tickets),
                    "max_results": max_results
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch tickets: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "message": f"❌ Error: {error_msg}"
            }
    
    def get_ticket_by_id(self, ticket_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific ticket by its key/ID.
        
        Args:
            ticket_key: The JIRA ticket key (e.g., 'PROJ-123')
            
        Returns:
            Dictionary containing detailed ticket information
        """
        try:
            logger.info(f"🔍 Fetching detailed information for ticket: {ticket_key}")
            
            # Get ticket using the JIRA client with all fields expanded
            jira_client = self.jira_agent.jira_client.jira
            issue = jira_client.issue(ticket_key, expand='changelog,comments,attachments,worklog')
            
            # Build comprehensive ticket information
            ticket_details = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description,
                'status': {
                    'name': issue.fields.status.name,
                    'category': issue.fields.status.statusCategory.name if issue.fields.status.statusCategory else None
                },
                'issue_type': {
                    'name': issue.fields.issuetype.name,
                    'subtask': issue.fields.issuetype.subtask if hasattr(issue.fields.issuetype, 'subtask') else False
                },
                'priority': {
                    'name': issue.fields.priority.name if issue.fields.priority else 'None',
                    'id': issue.fields.priority.id if issue.fields.priority else None
                },
                'project': {
                    'key': issue.fields.project.key,
                    'name': issue.fields.project.name
                },
                'assignee': {
                    'name': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'email': issue.fields.assignee.emailAddress if issue.fields.assignee else None,
                    'account_id': issue.fields.assignee.accountId if issue.fields.assignee else None
                },
                'reporter': {
                    'name': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                    'email': issue.fields.reporter.emailAddress if issue.fields.reporter else None
                },
                'dates': {
                    'created': issue.fields.created,
                    'updated': issue.fields.updated,
                    'due_date': issue.fields.duedate if hasattr(issue.fields, 'duedate') else None,
                    'resolution_date': issue.fields.resolutiondate if hasattr(issue.fields, 'resolutiondate') else None
                },
                'labels': list(issue.fields.labels) if issue.fields.labels else [],
                'components': [{'name': comp.name, 'id': comp.id} for comp in issue.fields.components] if issue.fields.components else [],
                'fix_versions': [{'name': version.name, 'id': version.id} for version in issue.fields.fixVersions] if issue.fields.fixVersions else [],
                'affects_versions': [{'name': version.name, 'id': version.id} for version in issue.fields.versions] if issue.fields.versions else []
            }
            
            # Add custom fields
            custom_fields = {}
            
            # Story points
            if hasattr(issue.fields, 'customfield_10016') and issue.fields.customfield_10016:
                custom_fields['story_points'] = issue.fields.customfield_10016
            
            # Epic link
            if hasattr(issue.fields, 'customfield_10014') and issue.fields.customfield_10014:
                custom_fields['epic_link'] = issue.fields.customfield_10014
            
            # Epic name (for Epic tickets)
            if hasattr(issue.fields, 'customfield_10011') and issue.fields.customfield_10011:
                custom_fields['epic_name'] = issue.fields.customfield_10011
            
            # Sprint information
            if hasattr(issue.fields, 'customfield_10020') and issue.fields.customfield_10020:
                custom_fields['sprint'] = str(issue.fields.customfield_10020)
            
            ticket_details['custom_fields'] = custom_fields
            
            # Add parent information for subtasks
            if hasattr(issue.fields, 'parent') and issue.fields.parent:
                ticket_details['parent'] = {
                    'key': issue.fields.parent.key,
                    'summary': issue.fields.parent.fields.summary,
                    'status': issue.fields.parent.fields.status.name,
                    'issue_type': issue.fields.parent.fields.issuetype.name
                }
            
            # Add subtasks information
            if hasattr(issue.fields, 'subtasks') and issue.fields.subtasks:
                ticket_details['subtasks'] = []
                for subtask in issue.fields.subtasks:
                    ticket_details['subtasks'].append({
                        'key': subtask.key,
                        'summary': subtask.fields.summary,
                        'status': subtask.fields.status.name,
                        'assignee': subtask.fields.assignee.displayName if subtask.fields.assignee else 'Unassigned'
                    })
            
            # Add comments
            if hasattr(issue.fields, 'comment') and issue.fields.comment.comments:
                ticket_details['comments'] = []
                for comment in issue.fields.comment.comments:
                    ticket_details['comments'].append({
                        'id': comment.id,
                        'author': comment.author.displayName,
                        'body': comment.body,
                        'created': comment.created,
                        'updated': comment.updated if hasattr(comment, 'updated') else comment.created
                    })
            
            # Add attachments
            if hasattr(issue.fields, 'attachment') and issue.fields.attachment:
                ticket_details['attachments'] = []
                for attachment in issue.fields.attachment:
                    ticket_details['attachments'].append({
                        'id': attachment.id,
                        'filename': attachment.filename,
                        'size': attachment.size,
                        'created': attachment.created,
                        'author': attachment.author.displayName
                    })
            
            # Add work logs
            if hasattr(issue.fields, 'worklog') and issue.fields.worklog.worklogs:
                ticket_details['worklogs'] = []
                for worklog in issue.fields.worklog.worklogs:
                    ticket_details['worklogs'].append({
                        'id': worklog.id,
                        'author': worklog.author.displayName,
                        'time_spent': worklog.timeSpent,
                        'time_spent_seconds': worklog.timeSpentSeconds,
                        'started': worklog.started,
                        'comment': worklog.comment if hasattr(worklog, 'comment') else None
                    })
            
            # Add changelog (history)
            if hasattr(issue, 'changelog') and issue.changelog.histories:
                ticket_details['history'] = []
                for history in issue.changelog.histories:
                    history_item = {
                        'id': history.id,
                        'author': history.author.displayName,
                        'created': history.created,
                        'items': []
                    }
                    
                    for item in history.items:
                        history_item['items'].append({
                            'field': item.field,
                            'field_type': item.fieldtype,
                            'from_value': item.fromString,
                            'to_value': item.toString
                        })
                    
                    ticket_details['history'].append(history_item)
            
            logger.info(f"✅ Retrieved detailed information for ticket: {ticket_key}")
            
            return {
                "success": True,
                "message": f"Retrieved detailed information for ticket {ticket_key}",
                "data": {
                    "ticket": ticket_details
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch ticket {ticket_key}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "message": f"❌ Error: {error_msg}"
            }


def main_process_json(json_input: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Main function to process JSON requirements - simple interface for external use.
    
    Args:
        json_input: JSON data as dictionary or string
        
    Returns:
        Processing result dictionary
    """
    try:
        handler = JiraHandler()
        return handler.process_json_requirements(json_input)
    except Exception as e:
        return {
            "success": False,
            "error": f"Handler initialization failed: {str(e)}",
            "message": f"❌ Error: Handler initialization failed: {str(e)}"
        }


def get_all_tickets(project_key: str = None, max_results: int = 50) -> Dict[str, Any]:
    """
    Get all tickets from JIRA - simple interface for external use.
    
    Args:
        project_key: Optional project key to filter tickets
        max_results: Maximum number of tickets to return
        
    Returns:
        Dictionary containing list of tickets
    """
    try:
        handler = JiraHandler()
        return handler.get_all_tickets(project_key, max_results)
    except Exception as e:
        return {
            "success": False,
            "error": f"Handler initialization failed: {str(e)}",
            "message": f"❌ Error: Handler initialization failed: {str(e)}"
        }


def get_ticket_details(ticket_key: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific ticket - simple interface for external use.
    
    Args:
        ticket_key: The JIRA ticket key (e.g., 'PROJ-123')
        
    Returns:
        Dictionary containing detailed ticket information
    """
    try:
        handler = JiraHandler()
        return handler.get_ticket_by_id(ticket_key)
    except Exception as e:
        return {
            "success": False,
            "error": f"Handler initialization failed: {str(e)}",
            "message": f"❌ Error: Handler initialization failed: {str(e)}"
        }


# Example usage and testing
if __name__ == "__main__":
    # Example JSON data for testing
    example_json = {
        "title": "User Authentication System",
        "businessObjective": "Implement secure user authentication",
        "functionalRequirements": [
            "User login with email and password",
            "Password reset functionality",
            "User session management"
        ],
        "nonFunctionalRequirements": {
            "security": "Passwords must be encrypted",
            "performance": "Login should complete within 2 seconds",
            "availability": "99.9% uptime required"
        },
        "userStories": [
            {
                "story": "As a user, I want to log in with my email and password so that I can access my account",
                "value": "Enable secure user access"
            },
            {
                "story": "As a user, I want to reset my password if I forget it so that I can regain access",
                "value": "Provide password recovery option"
            }
        ],
        "acceptanceCriteria": [
            "User can log in with valid credentials",
            "User receives error message for invalid credentials",
            "Password reset email is sent within 5 minutes"
        ],
        "assumptions": [
            "Users have valid email addresses",
            "Email service is available"
        ],
        "constraints": [
            "Must comply with GDPR",
            "Must use existing user database"
        ],
        "dependencies": [
            "Email service integration",
            "User database access"
        ],
        "assignee": {
            "dev": "Mihir Kanjaria",
        },
        "priority": "High",
        "suggestedJiraTasks": {
            "epic": "User Authentication System",
            "stories": [
                "User Login Implementation",
                "Password Reset Feature"
            ],
            "tasks": [
                "Design login UI",
                "Implement authentication API",
                "Add password encryption",
                "Create password reset flow",
                "Write unit tests",
                "Perform security testing"
            ]
        }
    }
    
    print("🧪 Testing JIRA Handler with example JSON...")
    print("=" * 60)
    
    try:
        # Test the main processing function
        result = main_process_json(example_json)
        
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success'] and 'data' in result:
            summary = result['data']['summary']
            print(f"\nSummary:")
            print(f"  Total Requested: {summary['total_requested']}")
            print(f"  Successfully Created: {summary['successfully_created']}")
            print(f"  Failed: {summary['failed']}")
            
            if result['data']['created_tickets']:
                print(f"\nCreated Tickets:")
                for ticket in result['data']['created_tickets']:
                    if ticket['success']:
                        print(f"  ✅ {ticket['ticket_key']}: {ticket['summary']}")
                    else:
                        print(f"  ❌ {ticket['summary']}: {ticket['error']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("=" * 60)
    print("Test completed.")
