# MTG Assistant

An AI-powered Magic: The Gathering assistant with rules lookup and card search capabilities.

## Features

- **Card Search**: Query MTG cards using Scryfall API
- **Rules Lookup**: Search official MTG rules and rulings
- **Chat Interface**: Interactive web-based chat UI
- **MCP Integration**: Modular tools via Model Context Protocol

## Quick Start

1. **Setup Environment**
   ```bash
   # Create .env file with your Claude API key
   echo "CLAUDE_API_KEY=your_key_here" > .env

   # Install Python dependencies
   pip install -r requirements.txt

   # Install frontend dependencies
   cd mtg-chat-frontend && npm install
   ```

2. **Start Services**
   ```bash
   # Run the startup script (Windows)
   scripts/start_servers.bat

   # Or start manually:
   # Terminal 1: python mcp/scryfall_mcp_server.py
   # Terminal 2: python mcp/mtg_rules_mcp_server.py
   # Terminal 3: python agents/mtg_server.py
   # Terminal 4: cd mtg-chat-frontend && npm run dev
   ```

3. **Open Browser**
   - Frontend: http://localhost:5173
   - API: http://localhost:8008

## Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + Strands Agent Framework
- **MCP Servers**: Scryfall API integration, MTG rules database
- **AI Model**: Claude 3.5 Haiku

## Usage

Ask questions like:
- "What does Lightning Bolt do?"
- "Show me blue counterspells under 3 mana"
- "What are the rules for combat damage?"

## Development

The project uses MCP (Model Context Protocol) for modular tool integration. Each MCP server provides specific capabilities that the AI agent can use to answer MTG-related questions.