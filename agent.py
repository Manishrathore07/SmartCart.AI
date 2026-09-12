"""
SmartCart Agent — CLI Runner
Use this to test the agent from the command line without the UI.
"""

import sys
import json
from brain import understand_query, pick_best_deal, summarize_comparison
from scraper import search_all
from memory import remember_search, get_stats
from webcmd_adapter import WebcmdClient

webcmd = WebcmdClient(profile="shopping")


def run_agent(query: str):
    print("\n" + "="*60)
    print("[SMARTCART] SmartCart Agent - Powered by Webcmd & Gemini")
    print("="*60)
    if webcmd.is_available():
        print("  [WEBCMD] Self-learning Browser Infra Connected (@agentrhq/webcmd v0.8.4)")
    else:
        print("  [WEBCMD] Running in local simulation mode")

    # Step 1: Understand
    print(f"\n[AI BRAIN] Understanding: '{query}'")
    query_info = understand_query(query)
    search_term = query_info.get("product_name", query)
    max_price = query_info.get("max_price")
    print(f"   -> Searching for: {search_term}")
    if max_price:
        print(f"   -> Budget: Rs. {max_price:,}")

    # Step 2: Search
    print(f"\n[BROWSER] Searching Amazon & Flipkart...")
    products = search_all(search_term, max_per_site=5)

    if max_price:
        products = [p for p in products if p.get("price", 999999) <= max_price]

    print(f"   -> Found {len(products)} products")

    if not products:
        print("[ERROR] No products found. Try a different search.")
        return

    # Step 3: Pick best
    print(f"\n[AI BRAIN] Gemini is analyzing deals...")
    winner = pick_best_deal(products, query)
    summary = summarize_comparison(products, winner)

    # Step 4: Display results
    print("\n" + "="*60)
    print("[RESULTS] PRICE COMPARISON")
    print("="*60)
    for i, p in enumerate(products[:8]):
        marker = "[WINNER]" if i == winner.get("winner_index", -1) else f"  {i+1}."
        print(f"{marker} [{p['site'].upper():8s}] Rs. {p['price']:>8,.0f} - {p['title'][:50]}")

    print("\n" + "="*60)
    print("[BEST DEAL]")
    print("="*60)
    wp = winner.get("winner_product", {})
    print(f"  Product : {wp.get('title', 'N/A')[:60]}")
    print(f"  Price   : Rs. {wp.get('price', 0):,.0f}")
    print(f"  Site    : {wp.get('site', 'N/A').upper()}")
    print(f"  Rating  : {wp.get('rating', 0):.1f} stars ({wp.get('review_count', 0):,} reviews)")
    print(f"  URL     : {wp.get('url', 'N/A')[:70]}")
    clean_summary = str(summary).replace('\u20b9', 'Rs. ')
    print(f"\n[AI Summary]: {clean_summary}")

    if winner.get("warning"):
        warn_msg = str(winner.get('warning', '')).replace('\u20b9', 'Rs. ')
        print(f"[WARNING]: {warn_msg}")

    remember_search(query, products, winner)

    # Stats
    stats = get_stats()
    print(f"\n[STATS] Total searches done: {stats['total_searches']}")
    print(f"[STATS] Total potential savings tracked: Rs. {stats['money_saved']:.2f}")
    print("="*60)

    # Step 5: Live Browser Agent & Human Approval
    url = wp.get("url")
    if not url or not url.startswith("http"):
        site = wp.get("site", "amazon").lower()
        if "flipkart" in site:
            url = f"https://www.flipkart.com/search?q={search_term.replace(' ', '+')}"
        else:
            url = f"https://www.amazon.in/s?k={search_term.replace(' ', '+')}"

    print("\n" + "="*60)
    print("[BROWSER AGENT] Live Browser Automation Ready!")
    print("="*60)
    print(f"  Product : {wp.get('title', 'Deal')[:50]}")
    print(f"  Store   : {wp.get('site', 'Amazon').upper()}")
    print(f"  URL     : {url[:70]}")
    print("  Action  : Launching live browser window on your screen...")

    import webbrowser
    webbrowser.open(url)
    print("  [SUCCESS] Browser window opened on your screen!")
    print("\n" + "#"*60)
    print("# [SAFEGUARD] HUMAN APPROVAL REQUIRED (Hackathon Safety Rule)")
    print("# The AI browser agent found the deal and navigated to it.")
    print("# You have 100% control - review the product and confirm checkout!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("What do you want to buy? -> ")

    run_agent(query)
