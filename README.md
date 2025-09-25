# Strands MCP Agent

A Python application that combines Strands agents with Fast MCP (Model Context Protocol) for containerized deployment on NAS systems.

## Features

- **Strands Agents**: AI-powered agents using Claude API
- **Fast MCP Integration**: Model Context Protocol server for tool integration
- **FastAPI Web Interface**: RESTful API for agent interactions
- **Docker Support**: Ready for containerization and NAS deployment
- **Health Monitoring**: Built-in health checks and logging

## Quick Start

### Local Development

1. **Install Dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
Make sure your `.env` file contains:
```
CLAUDE_API_KEY=your_claude_api_key_here
```

3. **Run the Application**
```bash
python app.py
```

The application will start on `http://localhost:8000`

### Docker Deployment

1. **Build and Run with Docker Compose**
```bash
docker-compose up --build
```

2. **Or build manually**
```bash
docker build -t strands-mcp-agent .
docker run -p 8000:8000 --env-file .env strands-mcp-agent
```

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `POST /agent/chat` - Chat with Strands agent

### Example Usage

```bash
curl -X POST "http://localhost:8000/agent/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, how can you help me?", "agent_type": "default"}'
```

## MCP Server

The Fast MCP server provides tools that can be integrated with the agents:

- `get_system_info` - Get system information
- `echo_message` - Echo messages back
- `process_data` - Process arbitrary data

Run the MCP server standalone:
```bash
python mcp/server.py
```

## Project Structure

```
├── agents/              # Strands agent implementations
├── mcp/                # Fast MCP server and tools
├── config/             # Configuration files
├── scripts/            # Utility scripts
├── tests/              # Test files
├── app.py              # Main FastAPI application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
└── docker-compose.yml  # Multi-container setup
```

## Configuration

### MCP Configuration
Edit `config/mcp_config.json` to configure MCP servers and tools.

### Environment Variables
- `CLAUDE_API_KEY` - Your Anthropic Claude API key
- `PORT` - Application port (default: 8000)

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Agents
1. Create new agent class in `agents/`
2. Implement the agent interface
3. Register in the main application

### Adding MCP Tools
1. Add tools to `mcp/server.py`
2. Update configuration in `config/mcp_config.json`
3. Test with the agent integration

## Deployment on NAS

This application is designed to run on NAS systems with Docker support:

1. Copy the project to your NAS
2. Ensure Docker and Docker Compose are installed
3. Run `docker-compose up -d` for background deployment
4. Access via your NAS IP on port 8000

## License

MIT License