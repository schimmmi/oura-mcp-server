# Claude Desktop Integration - Quick Setup

## ✅ Verified Working Configuration

This configuration has been tested and works with Claude Desktop.

### Step 1: Find Your Claude Config File

```bash
# macOS
open ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json

# Linux
nano ~/.config/Claude/claude_desktop_config.json
```

### Step 2: Add Oura MCP Server

**IMPORTANT:** Use the **absolute path to your venv Python**, not just `python`!

```json
{
  "mcpServers": {
    "oura": {
      "command": "/Users/jurgenschilling/workspace/oura-mcp-server/.venv/bin/python",
      "args": ["/Users/jurgenschilling/workspace/oura-mcp-server/main.py"],
      "env": {
        "OURA_ACCESS_TOKEN": "OXMQ5H4K7XBBIYEECRNBMGWIB2JYWL3X"
      }
    }
  }
}
```

**Replace with your paths:**
- Command: `<YOUR_PROJECT_PATH>/.venv/bin/python`
- Args: `["<YOUR_PROJECT_PATH>/main.py"]`
- Token: Your Oura access token

**Example template:**
```json
{
  "mcpServers": {
    "oura": {
      "command": "/full/path/to/oura-mcp-server/.venv/bin/python",
      "args": ["/full/path/to/oura-mcp-server/main.py"],
      "env": {
        "OURA_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

Completely quit and restart Claude Desktop for changes to take effect.

### Step 4: Verify Connection

In Claude Desktop, try asking:
- "What MCP servers are connected?"
- "How did I sleep last night?"
- "What's my readiness score today?"

You should see the Oura MCP server in the list and be able to query your health data.

## 🔍 Troubleshooting

### Error: "Failed to spawn process: No such file or directory"

**Problem:** Python path is incorrect or not absolute.

**Solution:** Use the full path to your venv Python:
```bash
# Find the correct path:
cd /path/to/oura-mcp-server
source .venv/bin/activate
which python
# Copy the output path and use it in your config
```

### Error: "Server transport closed unexpectedly"

**Problem:** Logging is going to stdout instead of stderr.

**Solution:** Already fixed in `config/config.yaml`:
```yaml
logging:
  output: "stderr"  # Must be stderr, not stdout!
```

### Server not showing up in Claude

1. Check config file syntax (valid JSON)
2. Verify paths are absolute, not relative
3. Ensure Claude Desktop was fully restarted
4. Check Claude Desktop logs:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### Test server manually

```bash
# Test if server starts correctly
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | /path/to/.venv/bin/python /path/to/main.py 2>/dev/null
```

Should return JSON response with server info.

## 📋 Complete Working Example

Here's a complete, working `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "oura": {
      "command": "/Users/jurgenschilling/workspace/oura-mcp-server/.venv/bin/python",
      "args": [
        "/Users/jurgenschilling/workspace/oura-mcp-server/main.py"
      ],
      "env": {
        "OURA_ACCESS_TOKEN": "OXMQ5H4K7XBBIYEECRNBMGWIB2JYWL3X"
      }
    }
  }
}
```

## ✨ Example Queries

Once connected, try these queries in Claude Desktop:

### Basic Queries
- "How did I sleep last night?"
- "What's my readiness score?"
- "Show me my activity for today"
- "Am I recovered enough for a workout?"

### Analysis Queries
- "Generate my daily health brief"
- "Analyze my sleep trend for the last week"
- "Why is my readiness score lower today?"
- "Compare my sleep from this week to last week"

### Available Resources
The server exposes these resources:
- `oura://sleep/today` - Last night's sleep
- `oura://sleep/yesterday` - Previous night
- `oura://readiness/today` - Today's readiness
- `oura://activity/today` - Today's activity

### Available Tools
- `generate_daily_brief` - Comprehensive health overview
- `analyze_sleep_trend` - Multi-day sleep analysis
- More tools coming in Phase 2!

## 🎯 Success Indicators

You'll know it's working when:
1. ✅ No errors in Claude Desktop logs
2. ✅ "oura" appears in connected MCP servers
3. ✅ Claude can answer questions about your health data
4. ✅ Responses include your actual Oura metrics

Enjoy your personal health AI assistant! 🎉
