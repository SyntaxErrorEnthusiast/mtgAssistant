from fastmcp import FastMCP
import chromadb
from sentence_transformers import SentenceTransformer
import os

mcp = FastMCP("MTGRules")

# Initialize once
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mtg_db", "chroma")
client = chromadb.PersistentClient(path=db_path)
model = SentenceTransformer('all-MiniLM-L6-v2')

@mcp.tool
def search_mtg_rules(query: str, n_results: int = 5) -> dict:
    """
    Search MTG Comprehensive Rules using vector similarity.

    Args:
        query: Natural language query about MTG rules
        n_results: Number of results to return (default 5)

    Returns:
        Dictionary with matching rule texts and metadata
    """
    try:
        collection = client.get_collection("mtg_rules")
        query_embedding = model.encode([query])

        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )

        return {
            "query": query,
            "results": [
                {
                    "text": doc,
                    "rule_number": meta.get("rule_number", ""),
                    "section": meta.get("section", ""),
                    "distance": dist
                }
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def get_specific_rule(rule_number: str) -> dict:
    """
    Get a specific MTG rule by number (e.g., "602.1a").

    Args:
        rule_number: Exact rule number to retrieve

    Returns:
        Dictionary with the specific rule text
    """
    try:
        collection = client.get_collection("mtg_rules")

        results = collection.query(
            query_texts=[rule_number],
            n_results=10,
            where={"rule_number": {"$eq": rule_number}}
        )

        if results['documents'][0]:
            return {
                "rule_number": rule_number,
                "text": results['documents'][0][0],
                "metadata": results['metadatas'][0][0]
            }
        else:
            return {"error": f"Rule {rule_number} not found"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)