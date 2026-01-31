# TickTick MCP Server (Security-Hardened Fork)

A **security-hardened** [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

> **This is a security-focused fork of [jacepark12/ticktick-mcp](https://github.com/jacepark12/ticktick-mcp)**

## Why This Fork?

The original TickTick MCP server had **9 security vulnerabilities** ranging from critical to medium severity. This fork addresses all of them:

| Severity | Vulnerability | Status |
|----------|--------------|--------|
| **Critical** | CSRF in OAuth callback - state parameter not validated | **Fixed** |
| **High** | Credentials stored with insecure file permissions | **Fixed** |
| **High** | OAuth server binds to all network interfaces | **Fixed** |
| **High** | No explicit TLS certificate verification | **Fixed** |
| **Medium** | Raw API errors exposed to users (info leakage) | **Fixed** |
| **Medium** | No rate limiting on OAuth callback server | **Fixed** |
| **Medium** | Bare except clause catches system signals | **Fixed** |
| **Medium** | Path traversal via unsanitized IDs in URLs | **Fixed** |
| **Medium** | Race conditions from global mutable state | **Fixed** |

### Security Improvements in Detail

**1. CSRF Protection (Critical)**
- OAuth state parameter is now validated on callback
- Attackers cannot trick users into authorizing malicious sessions

**2. Secure Credential Storage (High)**
- `.env` files are now created with `0600` permissions (owner read/write only)
- Other users on the system cannot read your tokens

**3. Localhost-Only Binding (High)**
- OAuth callback server now binds to `127.0.0.1` only
- Prevents remote attackers from intercepting OAuth callbacks

**4. Explicit TLS Verification (High)**
- All API requests now explicitly verify SSL certificates
- Prevents man-in-the-middle attacks

**5. Sanitized Error Messages (Medium)**
- API errors are logged but sanitized before showing to users
- Prevents accidental exposure of sensitive information

**6. Rate Limiting (Medium)**
- OAuth callback server limits requests to prevent DoS attacks
- Maximum 100 requests per authentication flow

**7. Input Validation (Medium)**
- All project/task IDs are validated before use in URLs
- Prevents path traversal attacks like `../admin`

**8. Proper Exception Handling (Medium)**
- Replaced bare `except:` with specific exception types
- System signals (Ctrl+C) now work correctly

**9. Thread-Safe State Management (Medium)**
- OAuth state is cleared before each new auth flow
- Prevents race conditions in concurrent usage

---

## Features

- View all your TickTick projects and tasks
- Create new projects and tasks through natural language
- Update existing task details (title, content, dates, priority)
- Mark tasks as complete
- Delete tasks and projects
- Full integration with TickTick's open API
- Seamless integration with Claude and other MCP clients
- **GTD (Getting Things Done) workflow support**

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret)

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/felores/ticktick-mcp-server.git
   cd ticktick-mcp-server
   ```

2. **Install with uv**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create a virtual environment
   uv venv

   # Activate the virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Install the package
   uv pip install -e .
   ```

3. **Authenticate with TickTick**:
   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

   This will:
   - Ask for your TickTick Client ID and Client Secret
   - Open a browser window for you to log in to TickTick
   - Automatically save your access tokens to a `.env` file with secure permissions

4. **Test your configuration**:
   ```bash
   uv run test_server.py
   ```

## Authentication with TickTick

This server uses OAuth2 to authenticate with TickTick:

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:
   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

3. Follow the prompts to enter your Client ID and Client Secret

4. A browser window will open for you to authorize the application

5. After authorizing, your access tokens will be securely saved to the `.env` file

The server handles token refresh automatically.

## Authentication with Dida365

[Dida365](https://dida365.com/home) is the China version of TickTick. To use it:

1. Register your application at the [Dida365 Developer Center](https://developer.dida365.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`

2. Add environment variables to your `.env` file:
   ```env
   TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
   TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
   TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
   ```

3. Follow the same authentication steps as for TickTick

## Usage with Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/download)

2. Edit your Claude for Desktop configuration file:

   **macOS**:
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add the TickTick MCP server configuration:
   ```json
   {
      "mcpServers": {
         "ticktick": {
            "command": "<absolute path to uv>",
            "args": ["run", "--directory", "<absolute path to ticktick-mcp-server directory>", "-m", "ticktick_mcp.cli", "run"]
         }
      }
   }
   ```

4. Restart Claude for Desktop

## Available MCP Tools

### Project Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `get_project_tasks` | List all tasks in a project | `project_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `delete_project` | Delete a project | `project_id` |

### Task Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_task` | Get details about a specific task | `project_id`, `task_id` |
| `create_task` | Create a new task | `title`, `project_id`, `content`, `start_date`, `due_date`, `priority` |
| `update_task` | Update an existing task | `task_id`, `project_id`, `title`, `content`, `start_date`, `due_date`, `priority` |
| `complete_task` | Mark a task as complete | `project_id`, `task_id` |
| `delete_task` | Delete a task | `project_id`, `task_id` |

### Task Retrieval & Search
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_all_tasks` | Get all tasks from all projects | None |
| `get_tasks_by_priority` | Get tasks filtered by priority level | `priority_id` (0: None, 1: Low, 3: Medium, 5: High) |
| `search_tasks` | Search tasks by title, content, or subtasks | `search_term` |

### Date-Based Task Retrieval
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_tasks_due_today` | Get all tasks due today | None |
| `get_tasks_due_tomorrow` | Get all tasks due tomorrow | None |
| `get_tasks_due_in_days` | Get tasks due in exactly X days | `days` |
| `get_tasks_due_this_week` | Get tasks due within the next 7 days | None |
| `get_overdue_tasks` | Get all overdue tasks | None |

### GTD (Getting Things Done) Framework
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_engaged_tasks` | Get "engaged" tasks (high priority or overdue) | None |
| `get_next_tasks` | Get "next" tasks (medium priority or due tomorrow) | None |
| `batch_create_tasks` | Create multiple tasks at once | `tasks` (list) |

## Example Prompts

### General
- "Show me all my TickTick projects"
- "Create a new task called 'Finish MCP server documentation' in my work project with high priority"
- "Mark the task 'Buy groceries' as complete"

### Task Filtering
- "What tasks do I have due today?"
- "Show me everything that's overdue"
- "Show me all my high priority tasks"

### GTD Workflow
- "Time block the rest of my day with items from my engaged list"
- "Walk me through my next actions for tomorrow"
- "Break down this project into 5 smaller actionable tasks"

## Project Structure

```bash
ticktick-mcp-server/
├── .env.template          # Template for environment variables
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── test_server.py         # Test script
└── ticktick_mcp/          # Main package
    ├── __init__.py
    ├── authenticate.py    # OAuth authentication utility
    ├── cli.py             # Command-line interface
    └── src/
        ├── __init__.py
        ├── auth.py        # OAuth implementation (security-hardened)
        ├── server.py      # MCP server implementation
        └── ticktick_client.py  # TickTick API client (security-hardened)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Credits

This is a security-hardened fork of [jacepark12/ticktick-mcp](https://github.com/jacepark12/ticktick-mcp). Thanks to the original author for creating the foundation of this project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
