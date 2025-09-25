import requests
from fastmcp import FastMCP

mcp = FastMCP("moxField")

DEFAULT_HEADERS = {
    "User-Agent": "DeckAgent/0.1 (+https://example.com)",
    "Accept": "application/json",
}

API = "https://api2.moxfield.com/v2/decks/all/{deck_id}"

@mcp.tool
def fetch_moxfield_deck(id: str, timeout=20) -> dict:
    """
    <tool>
        <name>fetch_moxfield_deck</name>
        <purpose>Search Moxfield for a deck using the deck ID and return compact, structured results.</purpose>
        <syntax>
            Use Search Moxfield: id: 4-fYtouFeEyALVnRsegnIQ
        </syntax>
        <examples>
            <ex>id="4-fYtouFeEyALVnRsegnIQ"</ex>
        </examples>
        <notes>
        </notes>
    </tool>
    """
    headers = {
        **DEFAULT_HEADERS,
        "Referer": f"https://www.moxfield.com/decks/{id}",
        "Origin":  "https://www.moxfield.com",
    }
    response = requests.get(API.format(deck_id=id), headers=headers, timeout=timeout)
    response.raise_for_status()  # raises for 4xx/5xx (403 if private/blocked)

    data = response.json()

    boards = ("commanders", "mainboard", "sideboard", "maybeboard")
    out = []
    for cat in boards:
        for card, details in data.get(cat, {}).items():
            out.append({
                "name": card,
                "quantity": details["quantity"],
                "mana_cost": details["card"]["mana_cost"],
                "type_line": details["card"]["type_line"],
                "cmc": details["card"]["cmc"],
                "colors": details["card"]["colors"],
                "rarity": details["card"]["rarity"],
                "boardType": details["boardType"],
                "price": details["card"].get("prices", {}).get("usd", 0.0),
                })
    return {"cards": out}


if __name__ == "__main__":
    mcp.run(transport="http", port=8001)