#!/usr/bin/env python3
"""
Sprint Agent API Client

Test client to interact with the Sprint Agent API server.
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("🩺 Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"📝 Message: {data['message']}")
            print("🔧 Components:")
            for component, status in data['components'].items():
                print(f"   {component}: {status}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    return True

def process_requirement(text: str):
    """Process a natural language requirement."""
    print(f"🔄 Processing requirement: {text}")
    try:
        payload = {"requirement": text}
        response = requests.post(f"{API_BASE_URL}/process", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['success']}")
            print(f"📝 Message: {data['message']}")
            
            if data.get('tasks'):
                print(f"\n📋 Generated Tasks ({len(data['tasks'])}):")
                for i, task in enumerate(data['tasks'], 1):
                    print(f"   {i}. {task}")
            
            if data.get('jira_keys'):
                print(f"\n🎫 JIRA Tickets ({len(data['jira_keys'])}):")
                for key in data['jira_keys']:
                    if key.startswith('ERROR'):
                        print(f"   ❌ {key}")
                    else:
                        print(f"   ✅ {key}")
            
            if data.get('data', {}).get('summary'):
                summary = data['data']['summary']
                print("\n📊 Summary:")
                print(f"   Tasks Generated: {summary.get('tasks_generated', 0)}")
                print(f"   Tickets Created: {summary.get('tickets_created', 0)}")
                print(f"   Errors: {summary.get('errors', 0)}")
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Error {response.status_code}: {error_detail}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def get_all_tickets():
    """Get all tickets from JIRA."""
    print("📋 Fetching all tickets...")
    try:
        response = requests.get(f"{API_BASE_URL}/tickets")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('tickets'):
                tickets = data['data']['tickets']
                print(f"✅ Found {len(tickets)} tickets:")
                for ticket in tickets[:5]:  # Show first 5
                    print(f"   🎫 {ticket['key']}: {ticket['summary']}")
                    print(f"      Status: {ticket['status']} | Type: {ticket['issue_type']}")
                if len(tickets) > 5:
                    print(f"   ... and {len(tickets) - 5} more tickets")
            else:
                print("❌ No tickets found or error occurred")
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Error {response.status_code}: {error_detail}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def interactive_mode():
    """Interactive mode for testing the API."""
    print("🤖 Sprint Agent API Client - Interactive Mode")
    print("Commands:")
    print("  - Type any requirement to process it")
    print("  - 'health' to check API health")
    print("  - 'tickets' to get all tickets")
    print("  - 'quit' to exit")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n💬 Enter command or requirement: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'health':
                test_health()
            elif user_input.lower() == 'tickets':
                get_all_tickets()
            elif user_input:
                process_requirement(user_input)
            else:
                print("⚠️ Please enter a command or requirement")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function."""
    print("🚀 Sprint Agent API Client")
    print("=" * 50)
    
    # Test connection first
    if not test_health():
        print("\n💡 Start the API server with: ./run_api.sh")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        # Command line mode
        requirement = " ".join(sys.argv[1:])
        process_requirement(requirement)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
