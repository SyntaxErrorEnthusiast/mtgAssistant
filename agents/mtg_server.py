import anyio
import asyncio
import contextlib
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.models.anthropic import AnthropicModel
from typing import Dict, List, Any, Tuple
from mcp.client.streamable_http import streamablehttp_client

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    pass

logger = logging.getLogger(__name__)
load_dotenv()

API_KEY = os.getenv("CLAUDE_API_KEY")
os.environ["BYPASS_TOOL_CONSENT"] = "true"

MCP_SERVERS = {
    "mtg_rules": "http://127.0.0.1:8000/mcp",
    "scryfall":  "http://127.0.0.1:8001/mcp",
    # "moxfield":  "http://127.0.0.1:8002/mcp",
}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """
<prompt>
  <role>
    You are an MTG assistant specialized in rules and deck synergy.
  </role>

  <context>
    The user is asking about Magic: The Gathering cards. Always verify the cards with Scryfall before answering. Anything rule relates should be verified using the proper tools
  </context>

  <critical_rules>
    - Never invent card text. If tool fails, say so.
    - Always cite tool results as the source of truth.
  </critical_rules>

  <tool_policy>
      1. Try `search_cards` first.
        1.a If you get a single card ensure to get it's ruling via `get_rulings`
      2. If no result, retry once more with a broader search
      3. If you get multiple results and the user is asking for a specific card, ask more questions
      4. If a user asks any questions regarding rules ensure to use the tool `search_mtg_rules`
  </tool_policy>

  <reasoning>
    - If multiple results appear, select the closest match by card name. Ask the user to clarify if uncertain.
    - Look for interactions between multiple cards
    - Analyze combo potential
    - Consider how cards work together strategically
    - Analyze how any information can be used if the user wants to build a deck
  </reasoning>

  <output_style>
    - Be concise, professional, and helpful. Use plain text. No emojis."
  </output_style>

  <examples>
    <ex>
        User: "What does Wilhelt do?" → Tool: search_cards("Wilhelt, the Rotcleaver") →
        Return: Name: name
                Mana Cost: mana_cost
                Text: oracle_text
                Price: prices
        </ex>
    <ex>User: "Show me UB zombies." → Tool: search_cards("t:creature t:zombie c:ub").</ex>
  </examples>
</prompt>

"""

# ---------- Models ----------
class ChatIn(BaseModel):
    session_id: str = "default"
    message: str

class ChatOut(BaseModel):
    reply: str

# ---------- Helpers ----------
def transport_factory(url: str):
    # MCPClient expects a zero-arg callable that returns an async ctx manager
    return (lambda: streamablehttp_client(url))

def connect_mcp_servers(servers: Dict[str, str]) -> Tuple[contextlib.ExitStack, List[Any]]:
    exit_stack = contextlib.ExitStack()
    all_tools: List[Any] = []
    for name, url in servers.items():
        try:
            client = MCPClient(transport_factory(url))
            exit_stack.enter_context(client)   # persistent connection
            tools = client.list_tools_sync()
            print(f"[MCP] {name}: loaded {len(tools)} tools")
            all_tools.extend(tools)
        except Exception as e:
            print(f"[MCP] {name}: failed to connect — {e}")
    return exit_stack, all_tools

def create_anthropic_model(system_prompt="", temperature=0.3):
    """Helper function to create Anthropic models with consistent config"""
    return AnthropicModel(
        client_args={
            "api_key": API_KEY,
        },
        max_tokens=1028,
        model_id="claude-3-5-haiku-20241022",
        # model_id="claude-sonnet-4-0",
        params={
            "temperature": temperature,
            "system": system_prompt
        }
    )

def create_app() -> FastAPI:
    app = FastAPI(title="MTG Chat (Strands + MCP + Ollama)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Startup: connect MCP + build agent
    exit_stack, tools = connect_mcp_servers(MCP_SERVERS)
    agent = Agent(
        model=create_anthropic_model(system_prompt=SYSTEM_PROMPT),
        tools=tools,
    )
    # keep state on app
    app.state.exit_stack = exit_stack
    app.state.agent = agent
    app.state.sessions: Dict[str, List[Dict[str, Any]]] = {}

    @app.on_event("shutdown")
    def _shutdown():
        try:
            app.state.exit_stack.close()
            print("[MCP] disconnected")
        except Exception:
            pass

    @app.post("/chat", response_model=ChatOut)
    def chat(body: ChatIn):
        # lightweight domain gate; the prompt already enforces MTG-only
        banned = ["weather", "politics", "python", "stocks", "crypto", "kotlin", "aws "]
        if any(b in body.message.lower() for b in banned):
            return ChatOut(reply="I only answer Magic: The Gathering questions. What MTG topic can I help with?")

        app.state.sessions.setdefault(body.session_id, []).append({"role": "user", "content": body.message})
        try:
            result = app.state.agent(body.message)
            reply = str(result)
        except Exception as e:
            reply = f"Agent error: {e}"
        app.state.sessions[body.session_id].append({"role": "assistant", "content": reply})
        return ChatOut(reply=reply)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Use the module path to enable --reload behavior
    uvicorn.run("mtg_server:app", host="127.0.0.1", port=8008, reload=True)