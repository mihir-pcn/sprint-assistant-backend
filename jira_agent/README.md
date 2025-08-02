# JIRA Handler - Source Code

This `src/` folder contains the essential files for the JIRA Handler functionality.

## Files Included

### Core Handler

- **`handler.py`** - Main handler interface with ticket viewing functions
  - `get_all_tickets()` - Get all tickets from JIRA project
  - `get_ticket_details()` - Get detailed information for specific ticket

### Dependencies

- **`json_processor.py`** - JSON processing and validation
- **`jira_agent.py`** - High-level JIRA operations and business logic
- **`jira_client.py`** - Low-level JIRA API client
- **`config.py`** - Configuration management
- **`models.py`** - Data models and type definitions

### Configuration

- **`.env`** - Environment variables (JIRA credentials)
- **`requirements.txt`** - Python package dependencies

## Usage

```python
import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Use the handler
from handler import get_all_tickets, get_ticket_details

# Get all tickets
tickets = get_all_tickets(max_results=10)

# Get specific ticket details
details = get_ticket_details('TEST-131')
```

## Dependencies Required

Install dependencies using the included requirements file:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install jira python-dotenv pydantic typing-extensions requests
```

## Notes

- All files are self-contained within this `src/` folder
- No test files, logs, or documentation included (only source code)
- Ready for production use or integration into other projects
