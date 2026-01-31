# TickTick MCP Server

A **security-hardened** [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables managing your tasks directly through any MCP-compatible client.

[![PyPI version](https://badge.fury.io/py/ticktick-mcp-server.svg)](https://pypi.org/project/ticktick-mcp-server/)

## Works With Any MCP Client

This server works with **any MCP-compatible client** — just one command:

```bash
uvx ticktick-mcp-server
```

That's it. No complex setup, no dependencies to manage. Works with:
- **Claude Desktop**
- **Cursor**
- **Cline**
- **Continue**
- **Any MCP-compatible IDE or tool**

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- TickTick account
- TickTick API credentials ([get them here](https://developer.ticktick.com/manage))

## Quick Start

### 1. Get TickTick API Credentials

1. Go to [TickTick Developer Center](https://developer.ticktick.com/manage)
2. Create a new app with redirect URI: `http://localhost:8080/callback`
3. Copy your **Client ID** and **Client Secret**

### 2. Configure Your MCP Client

Add this to your MCP client config:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "uvx",
      "args": ["ticktick-mcp-server"]
    }
  }
}
```

<details>
<summary><strong>Config file locations</strong></summary>

| Client | macOS | Windows |
|--------|-------|---------|
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` | `%USERPROFILE%\.cursor\mcp.json` |
| Cline | VSCode settings | VSCode settings |

</details>

### 3. Authenticate

Run once to connect your TickTick account:

```bash
uvx ticktick-mcp-server auth
```

### 4. Restart Your Client

That's it! Now you can:
- "Show me all my TickTick projects"
- "What tasks are due today?"
- "Create a task to buy groceries in my Shopping list"

---

## Alternative Installation

### Using pip

```bash
pip install ticktick-mcp-server
ticktick-mcp-server auth
```

Then use in Claude Desktop config:
```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp-server"
    }
  }
}
```

### From Source

```bash
git clone https://github.com/felores/ticktick-mcp-server.git
cd ticktick-mcp-server
uv pip install -e .
```

---

## Dida365 (滴答清单) Support

For the China version of TickTick, add these to your `.env` file:

```env
TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
```

Register your app at [Dida365 Developer Center](https://developer.dida365.com/manage).

---

## Available Tools

### Projects
| Tool | Description |
|------|-------------|
| `get_projects` | List all projects |
| `get_project` | Get project details |
| `create_project` | Create a new project |
| `delete_project` | Delete a project |

### Tasks
| Tool | Description |
|------|-------------|
| `get_task` | Get task details |
| `create_task` | Create a new task |
| `update_task` | Update a task |
| `complete_task` | Mark task complete |
| `delete_task` | Delete a task |
| `get_all_tasks` | Get all tasks |
| `search_tasks` | Search tasks |

### Date Filters
| Tool | Description |
|------|-------------|
| `get_tasks_due_today` | Tasks due today |
| `get_tasks_due_tomorrow` | Tasks due tomorrow |
| `get_tasks_due_this_week` | Tasks due this week |
| `get_overdue_tasks` | Overdue tasks |

### GTD Workflow
| Tool | Description |
|------|-------------|
| `get_engaged_tasks` | High priority + overdue |
| `get_next_tasks` | Medium priority + due tomorrow |
| `batch_create_tasks` | Create multiple tasks |

---

## Example Prompts

```bash
"Show me all my TickTick projects"
"What tasks do I have due today?"
"Create a high priority task 'Finish report' in my Work project"
"Mark 'Buy groceries' as complete"
"Show me everything that's overdue"
"Break down 'Plan vacation' into 5 subtasks"
```

---

## Why This Fork?

This is a security-hardened fork of [jacepark12/ticktick-mcp](https://github.com/jacepark12/ticktick-mcp) with **9 vulnerabilities fixed**:

| Severity | Issue | Status |
|----------|-------|--------|
| **Critical** | CSRF in OAuth callback | Fixed |
| **High** | Insecure credential file permissions | Fixed |
| **High** | OAuth server binds to all interfaces | Fixed |
| **High** | No explicit TLS verification | Fixed |
| **Medium** | Sensitive data in error messages | Fixed |
| **Medium** | No rate limiting on OAuth | Fixed |
| **Medium** | Bare except catches signals | Fixed |
| **Medium** | Path traversal in IDs | Fixed |
| **Medium** | Race conditions in state | Fixed |

---

## License

MIT License - see LICENSE file for details.

## Credits

Fork of [jacepark12/ticktick-mcp](https://github.com/jacepark12/ticktick-mcp).
