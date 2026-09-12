"""
SmartCart Agent — Memory System (webcmd-style self-learning)
Saves learned workflows per site so the agent improves over time.
"""

import json
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = "memory.json"


def load_memory() -> dict:
    """Load saved memory from disk."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "searches": [],
        "learned_workflows": {},
        "price_history": {},
        "stats": {"total_searches": 0, "money_saved": 0}
    }


def save_memory(memory: dict):
    """Save memory to disk."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def remember_search(query: str, products: list, winner: dict):
    """Save search results to memory."""
    memory = load_memory()
    memory["searches"].append({
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "total_products_found": len(products),
        "winner_site": winner.get("winner_product", {}).get("site", ""),
        "winner_price": winner.get("winner_product", {}).get("price", 0),
    })
    memory["stats"]["total_searches"] += 1

    # Track potential savings
    if products:
        prices = [p.get("price", 0) for p in products if p.get("price", 0) > 0]
        if prices:
            max_price = max(prices)
            win_price = winner.get("winner_product", {}).get("price", max_price)
            saved = max_price - win_price
            memory["stats"]["money_saved"] += saved

    save_memory(memory)


def learn_workflow(site: str, workflow_name: str, steps: list):
    """
    webcmd-style: Save a learned workflow for a site.
    Next time we visit this site, we already know what to do!
    """
    memory = load_memory()
    if site not in memory["learned_workflows"]:
        memory["learned_workflows"][site] = {}

    memory["learned_workflows"][site][workflow_name] = {
        "steps": steps,
        "learned_at": datetime.now().isoformat(),
        "success_count": 1
    }
    save_memory(memory)
    print(f"🧠 Learned workflow '{workflow_name}' for {site}")


def get_workflow(site: str, workflow_name: str) -> list:
    """Retrieve a previously learned workflow."""
    memory = load_memory()
    workflows = memory.get("learned_workflows", {}).get(site, {})
    if workflow_name in workflows:
        wf = workflows[workflow_name]
        # Increment success count
        wf["success_count"] = wf.get("success_count", 0) + 1
        save_memory(memory)
        print(f"🔁 Reusing learned workflow '{workflow_name}' for {site}")
        return wf["steps"]
    return []


def track_price(product_title: str, site: str, price: float):
    """Track price history for a product."""
    memory = load_memory()
    key = f"{site}:{product_title[:50]}"
    if key not in memory["price_history"]:
        memory["price_history"][key] = []
    memory["price_history"][key].append({
        "price": price,
        "date": datetime.now().isoformat()
    })
    save_memory(memory)


def get_stats() -> dict:
    """Get overall stats for the stats panel."""
    memory = load_memory()
    return {
        "total_searches": memory["stats"]["total_searches"],
        "money_saved": round(memory["stats"]["money_saved"], 2),
        "learned_sites": list(memory.get("learned_workflows", {}).keys()),
        "recent_searches": memory["searches"][-5:][::-1]
    }


if __name__ == "__main__":
    stats = get_stats()
    print("[STATS] SmartCart Memory Stats:")
    print(f"  Total searches: {stats['total_searches']}")
    print(f"  Money saved: Rs. {stats['money_saved']:.2f}")
    print(f"  Learned sites: {stats['learned_sites']}")
