#!/usr/bin/env python3
"""
Configuration management for JIRA AI Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for JIRA AI Agent"""
    
    # JIRA Configuration
    JIRA_SERVER = os.getenv('JIRA_SERVER')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'TEST')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration values are present"""
        required_vars = [
            'JIRA_SERVER',
            'JIRA_USERNAME', 
            'JIRA_API_TOKEN',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        return True
