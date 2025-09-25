# MTG Rules Search UI

A simple React interface for searching MTG Comprehensive Rules using the MCP server.

## Setup

1. Install dependencies:
```bash
cd ui
npm install
```

2. Start the MCP server (from project root):
```bash
python mcp/mtg_rules_mcp_server.py
```

3. Start the API bridge (from project root):
```bash
python api_bridge.py
```

4. Start the React app:
```bash
cd ui
npm start
```

The app will open at http://localhost:3000

## Features

- **Search Rules**: Natural language search through MTG rules using vector similarity
- **Get Specific Rule**: Look up exact rule numbers (e.g., "602.1a")
- Clean, responsive interface
- Real-time search results with similarity scores

## Usage

1. Use the "Search Rules" tab to ask questions like:
   - "How does flying work?"
   - "What happens when a creature dies?"
   - "Priority rules"

2. Use the "Get Specific Rule" tab to look up exact rule numbers:
   - 100.1 (general game concepts)
   - 602.1a (casting spells)
   - 702.9a (flying ability)

## Architecture

- React frontend (port 3000)
- Flask API bridge (port 5000) 
- MCP server (port 8003)
- ChromaDB vector database