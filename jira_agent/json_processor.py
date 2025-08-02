#!/usr/bin/env python3
"""
JSON Processor for JIRA AI Agent

Processes structured JSON input from product analysis and converts it to JIRA tickets.
Replaces the natural language processing with direct JSON structure processing.
"""

import logging
from typing import Dict, Any, List, Optional
from models import TicketRequest, TicketType, TicketPriority
import json

logger = logging.getLogger(__name__)

class JSONProcessor:
    """Processes structured JSON input and converts to JIRA ticket requests"""
    
    def __init__(self):
        """Initialize the JSON processor"""
        self.logger = logging.getLogger(__name__)
    
    def process_json_input(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process structured JSON input and convert to JIRA ticket creation requests
        
        Args:
            json_data: Structured JSON from product analyst
            
        Returns:
            Dict containing ticket creation instructions and metadata
        """
        try:
            # Validate required fields
            if not self._validate_json_structure(json_data):
                return {
                    'success': False,
                    'error': 'Invalid JSON structure. Missing required fields.',
                    'action': 'error'
                }
            
            # Extract basic information
            title = json_data.get('title', '')
            business_objective = json_data.get('businessObjective', '')
            priority = json_data.get('priority', 'Medium').title()
            assignee = json_data.get('assignee', {})
            
            # Convert to JIRA priority enum
            try:
                jira_priority = TicketPriority(priority)
            except ValueError:
                jira_priority = TicketPriority.MEDIUM
                logger.warning(f"Invalid priority '{priority}', defaulting to Medium")
            
            # Process suggested JIRA tasks
            suggested_tasks = json_data.get('suggestedJiraTasks', {})
            
            # Create ticket requests based on the structure
            ticket_requests = []
            
            # 1. Create Epic if specified
            epic_title = suggested_tasks.get('epic')
            if epic_title:
                epic_request = self._create_epic_request(
                    title=epic_title,
                    description=self._build_epic_description(json_data),
                    assignee=assignee.get('dev'),
                    json_data=json_data
                )
                ticket_requests.append(epic_request)
            
            # 2. Create Stories
            stories = suggested_tasks.get('stories', [])
            for story_title in stories:
                story_request = self._create_story_request(
                    title=story_title,
                    description=self._build_story_description(story_title, json_data),
                    priority=jira_priority,
                    assignee=assignee.get('dev'),
                    json_data=json_data
                )
                ticket_requests.append(story_request)
            
            # 3. Create Tasks
            tasks = suggested_tasks.get('tasks', [])
            for task_title in tasks:
                task_request = self._create_task_request(
                    title=task_title,
                    description=self._build_task_description(task_title, json_data),
                    priority=jira_priority,
                    assignee=assignee.get('dev'),
                    json_data=json_data
                )
                ticket_requests.append(task_request)
            
            return {
                'success': True,
                'action': 'create_multiple',
                'explanation': f'Creating {len(ticket_requests)} JIRA tickets from structured requirements',
                'data': {
                    'ticket_requests': ticket_requests,
                    'summary': {
                        'total_tickets': len(ticket_requests),
                        'epic_count': 1 if epic_title else 0,
                        'story_count': len(stories),
                        'task_count': len(tasks)
                    },
                    'source_data': {
                        'title': title,
                        'business_objective': business_objective,
                        'priority': priority,
                        'assignee': assignee
                    }
                },
                'confidence': 1.0
            }
            
        except Exception as e:
            logger.error(f"Error processing JSON input: {e}")
            return {
                'success': False,
                'error': f'Failed to process JSON input: {str(e)}',
                'action': 'error'
            }
    
    def _validate_json_structure(self, json_data: Dict[str, Any]) -> bool:
        """Validate that the JSON has the expected structure"""
        required_fields = ['title', 'businessObjective', 'suggestedJiraTasks']
        
        for field in required_fields:
            if field not in json_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate suggestedJiraTasks structure
        suggested_tasks = json_data.get('suggestedJiraTasks', {})
        if not isinstance(suggested_tasks, dict):
            logger.error("suggestedJiraTasks must be an object")
            return False
        
        return True
    
    def _create_epic_request(self, title: str, description: str, assignee: Optional[str], json_data: Dict[str, Any]) -> TicketRequest:
        """Create a JIRA Epic request"""
        return TicketRequest(
            summary=f"Epic: {title}",
            description=description,
            project_key="TEST",  # This should be configurable or detected
            issue_type=TicketType.EPIC,
            priority=None,  # Epics don't have priority in most JIRA configurations
            assignee=assignee,
            labels=self._extract_labels(json_data)
        )
    
    def _create_story_request(self, title: str, description: str, priority: TicketPriority, assignee: Optional[str], json_data: Dict[str, Any]) -> TicketRequest:
        """Create a JIRA Story request"""
        return TicketRequest(
            summary=title,
            description=description,
            project_key="TEST",  # This should be configurable or detected
            issue_type=TicketType.STORY,
            priority=priority,
            assignee=assignee,
            labels=self._extract_labels(json_data)
        )
    
    def _create_task_request(self, title: str, description: str, priority: TicketPriority, assignee: Optional[str], json_data: Dict[str, Any]) -> TicketRequest:
        """Create a JIRA Task request"""
        return TicketRequest(
            summary=title,
            description=description,
            project_key="TEST",  # This should be configurable or detected
            issue_type=TicketType.TASK,
            priority=priority,
            assignee=assignee,
            labels=self._extract_labels(json_data)
        )
    
    def _build_epic_description(self, json_data: Dict[str, Any]) -> str:
        """Build description for Epic ticket"""
        title = json_data.get('title', '')
        business_objective = json_data.get('businessObjective', '')
        functional_reqs = json_data.get('functionalRequirements', [])
        non_functional_reqs = json_data.get('nonFunctionalRequirements', {})
        
        description = f"# {title}\n\n"
        description += f"## Business Objective\n{business_objective}\n\n"
        
        if functional_reqs:
            description += "## Functional Requirements\n"
            for req in functional_reqs:
                description += f"- {req}\n"
            description += "\n"
        
        if non_functional_reqs:
            description += "## Non-Functional Requirements\n"
            for category, requirement in non_functional_reqs.items():
                description += f"- **{category.title()}**: {requirement}\n"
            description += "\n"
        
        # Add user stories if available
        user_stories = json_data.get('userStories', [])
        if user_stories:
            description += "## User Stories\n"
            for story in user_stories:
                story_text = story.get('story', '') if isinstance(story, dict) else str(story)
                value = story.get('value', '') if isinstance(story, dict) else ''
                description += f"- {story_text}"
                if value:
                    description += f" (Value: {value})"
                description += "\n"
        
        return description
    
    def _build_story_description(self, title: str, json_data: Dict[str, Any]) -> str:
        """Build description for Story ticket"""
        # Find matching user story
        user_stories = json_data.get('userStories', [])
        matching_story = None
        
        for story in user_stories:
            if isinstance(story, dict):
                story_text = story.get('story', '')
                if title.lower() in story_text.lower() or story_text.lower() in title.lower():
                    matching_story = story
                    break
        
        description = f"# {title}\n\n"
        
        if matching_story:
            description += f"## User Story\n{matching_story.get('story', '')}\n\n"
            value = matching_story.get('value', '')
            if value:
                description += f"## Value\n{value}\n\n"
        
        # Add acceptance criteria
        acceptance_criteria = json_data.get('acceptanceCriteria', [])
        if acceptance_criteria:
            description += "## Acceptance Criteria\n"
            for criteria in acceptance_criteria:
                if title.lower() in criteria.lower():
                    description += f"- {criteria}\n"
            description += "\n"
        
        # Add business context
        business_objective = json_data.get('businessObjective', '')
        if business_objective:
            description += f"## Business Context\n{business_objective}\n\n"
        
        return description
    
    def _build_task_description(self, title: str, json_data: Dict[str, Any]) -> str:
        """Build description for Task ticket"""
        description = f"# {title}\n\n"
        
        # Add relevant functional requirements
        functional_reqs = json_data.get('functionalRequirements', [])
        relevant_reqs = [req for req in functional_reqs if any(word in req.lower() for word in title.lower().split())]
        
        if relevant_reqs:
            description += "## Related Requirements\n"
            for req in relevant_reqs:
                description += f"- {req}\n"
            description += "\n"
        
        # Add constraints and assumptions
        constraints = json_data.get('constraints', [])
        if constraints and constraints != ["None"]:
            description += "## Constraints\n"
            for constraint in constraints:
                description += f"- {constraint}\n"
            description += "\n"
        
        assumptions = json_data.get('assumptions', [])
        if assumptions:
            description += "## Assumptions\n"
            for assumption in assumptions:
                description += f"- {assumption}\n"
            description += "\n"
        
        # Add dependencies
        dependencies = json_data.get('dependencies', [])
        if dependencies and dependencies != ["None"]:
            description += "## Dependencies\n"
            for dependency in dependencies:
                description += f"- {dependency}\n"
            description += "\n"
        
        return description
    
    def _extract_labels(self, json_data: Dict[str, Any]) -> List[str]:
        """Extract labels from JSON data"""
        labels = []
        
        # Add priority as label
        priority = json_data.get('priority', '').lower()
        if priority:
            labels.append(f"priority-{priority}")
        
        # Add assignee info as labels
        assignee = json_data.get('assignee', {})
        if assignee.get('dev'):
            labels.append("development")
        if assignee.get('qa'):
            labels.append("testing")
        
        # Add other relevant labels
        non_functional_reqs = json_data.get('nonFunctionalRequirements', {})
        for category in non_functional_reqs.keys():
            labels.append(category.lower())
        
        return labels
