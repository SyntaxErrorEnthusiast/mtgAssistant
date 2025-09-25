from typing import Literal, Dict, Any, List
import httpx
import logging
from fastmcp import FastMCP
from helpers.api_helper import scryfall_get

# Configure logging to prevent FastMCP logging conflicts
logging.basicConfig(level=logging.WARNING)

mcp = FastMCP("scryfall")

def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(n, hi))

def _err(message: str) -> Dict[str, Any]:
    return {"ok": False, "error": message}

@mcp.tool
async def search_cards(
    query: str,
    order: Literal[
        "name","set","released","rarity","color","usd","tix","eur",
        "cmc","power","toughness","edhrec","penny","artist","review"
    ] = "name",
    direction: Literal["auto","asc","desc"] = "auto",
    include_extras: bool = False,
    page: int = 1,
    sample_size: int = 5,
    verbosity: Literal["summary","full"] = "summary",
) -> Dict[str, Any]:
    """
    <tool>
        <name>search_cards</name>
        <purpose>Search MTG cards on Scryfall and return compact, structured results.</purpose>
        <syntax>
            Use Scryfall search: t:creature, t:zombie, c:ub, o:"draw a card", pow>=3 tou>=5
        </syntax>
        <examples>
            <ex>query="t:zombie t:creature"</ex>
            <ex>query="t:instant c:blue"</ex>
            <ex>query="t:creature c:red pow=3", order="cmc", direction="asc"</ex>
        </examples>
        <notes>
            sample_size is clamped to 1–10 to keep outputs small for Qwen3:8b.
            Use has_more/next_page to continue pagination.
        </notes>
    </tool>
    """

    # Query Validation
    query = (query or "").strip()
    if len(query) < 2:
        return _err("Query must be at least 2 characters.")

    page = max(1, page)
    sample_size = _clamp(sample_size, 1, 10)

    params = {
        "q": query,
        "order": order,
        "dir": direction,
        "page": page,
        **({"include_extras": "true"} if include_extras else {}),
    }

    # Hitting scryfall api helper method that has a builtin rate limiter
    try:
        async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": "fastmcp-scryfall/0.1"}) as c:
            resp = await scryfall_get(c, params=params)
    except httpx.HTTPError as e:
        return _err(f"Network error: {type(e).__name__}")

    if resp.status_code != 200:
        # Scryfall returns helpful JSON; fall back to text if not JSON
        try:
            details = resp.json().get("details", resp.text)
        except ValueError:
            details = resp.text
        return _err(f"HTTP {resp.status_code}: {details[:400]}")

    try:
        payload = resp.json()
    except ValueError:
        return _err("Invalid JSON from Scryfall.")

    data: List[Dict[str, Any]] = payload.get("data", [])
    total = payload.get("total_cards")
    has_more = bool(payload.get("has_more", False))
    next_page = payload.get("next_page")

    # Build a compact sample, with sensible face/image fallbacks
    sample: List[Dict[str, Any]] = []
    for card in data[:sample_size]:
        faces = card.get("card_faces") or []
        face0 = faces[0] if faces else {}
        image_uris = card.get("image_uris") or face0.get("image_uris") or {}
        sample.append({
            "id": card.get("id"),
            "name": card.get("name"),
            "mana_cost": card.get("mana_cost") or face0.get("mana_cost"),
            "type_line": card.get("type_line") or face0.get("type_line"),
            "oracle_text": card.get("oracle_text") or face0.get("oracle_text"),
            "cmc": card.get("cmc"),
            "colors": card.get("colors"),
            "color_identity": card.get("color_identity"),
            "rarity": card.get("rarity"),
            "set": card.get("set"),
            "scryfall_uri": card.get("scryfall_uri"),
            "prices": card.get("prices").get("usd"),
            "image_url": (
                image_uris.get("normal")
                or image_uris.get("large")
                or image_uris.get("small")
            ),
        })

    return {
        "ok": True,
        "query": query,
        "order": order,
        "direction": direction,
        "page": page,
        "total_cards": total,
        "has_more": has_more,
        "next_page": next_page,
        "count": len(data),
        "sample": sample if verbosity == "summary" else data,
        **({"warnings": payload.get("warnings")[:5]} if payload.get("warnings") else {}),
    }

@mcp.tool
async def get_rulings(
    id: str,
) -> Dict[str, Any]:
    """
    <tool>
        <name>get_rulings</name>
        <purpose>Search MTG card rulings on Scryfall and return compact, structured results. Finds cards based on the card's scrfall id</purpose>
        <syntax>
            Use Scryfall Rulings: id: f2b9983e-20d4-4d12-9e2c-ec6d9a345787
        </syntax>
        <when_to_use>
            - User asks "how does X work with Y"
            - Questions about card interactions or synergies
            - Rules clarifications needed
            - User mentions "rulings" or "official rules"
            - Complex card mechanics need explanation
            - After finding a card, if the user asks follow-up questions about how it works
        </when_to_use>
        <examples>
            <ex>id="f2b9983e-20d4-4d12-9e2c-ec6d9a345787"</ex>
            <ex>id="d99a9a7d-d9ca-4c11-80ab-e39d5943a315"</ex>
            <ex>User asks: "How does Gravecrawler work with sacrifice outlets?" → Use get_rulings for Gravecrawler</ex>
            <ex>User asks: "Do ETB effects trigger for token copies?" → Use get_rulings for the relevant card</ex>
            <ex>User asks: "What are the official rulings on this card?" → Use get_rulings</ex>
        </examples>
        <notes>
            Use has_more/next_page to continue pagination.
        </notes>
    </tool>
    """


    # Hitting scryfall api helper method that has a builtin rate limiter
    url =  f"https://api.scryfall.com/cards/{id}/rulings"
    try:
        async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": "fastmcp-scryfall/0.1"}) as c:
            resp = await scryfall_get(c, url=url)
    except httpx.HTTPError as e:
        return _err(f"Network error: {type(e).__name__}")

    if resp.status_code != 200:
        # Scryfall returns helpful JSON; fall back to text if not JSON
        try:
            details = resp.json().get("details", resp.text)
        except ValueError:
            details = resp.text
        return _err(f"HTTP {resp.status_code}: {details[:400]}")

    try:
        payload = resp.json()
    except ValueError:
        return _err("Invalid JSON from Scryfall.")

    data: List[Dict[str, Any]] = payload.get("data", [])
    total = payload.get("total_cards")
    has_more = bool(payload.get("has_more", False))

    # Build a compact sample, with sensible face/image fallbacks
    sample: List[Dict[str, Any]] = []
    for ruling in data:

        sample.append({
            "id": ruling.get("oracle_id"),
            "source": ruling.get("source"),
            "published": ruling.get("published_at"),
            "ruling": ruling.get("comment"),
        })

    return {
        "ok": True,
        "id": id,
        "count": len(data),
        "sample": sample,
        **({"warnings": payload.get("warnings")[:5]} if payload.get("warnings") else {}),
    }

# if __name__ == "__main__":
#     mcp.run()


if __name__ == "__main__":
    mcp.run(transport="http", port=8001)