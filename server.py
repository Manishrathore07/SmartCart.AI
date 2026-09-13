"""
SmartCart Agent — Localhost Web Server & Frontend
Powered by FastAPI, Uvicorn, Google Gemini, and Webcmd.
"""

import os
import sys
import webbrowser
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain import understand_query, pick_best_deal, summarize_comparison, ask_about_deal
from scraper import search_all
from memory import remember_search, get_stats, add_to_watchlist, get_watchlist
from webcmd_adapter import WebcmdClient

app = FastAPI(title="SmartCart AI Browser Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

webcmd = WebcmdClient(profile="shopping")


class SearchRequest(BaseModel):
    query: str


class LaunchRequest(BaseModel):
    url: str
    site: Optional[str] = "amazon"
    title: Optional[str] = "Product"


class AskRequest(BaseModel):
    product: dict
    question: str


class WatchlistRequest(BaseModel):
    product: dict
    target_price: Optional[float] = None


@app.get("/api/stats")
def api_stats():
    stats = get_stats()
    stats["webcmd_connected"] = webcmd.is_available()
    return stats


@app.post("/api/ask")
def api_ask(req: AskRequest):
    answer = ask_about_deal(req.product, req.question)
    return {"success": True, "answer": answer}


@app.post("/api/watchlist")
def api_add_watchlist(req: WatchlistRequest):
    item = add_to_watchlist(req.product, req.target_price)
    return {
        "success": True, 
        "item": item, 
        "message": f"Added to watchlist at target price Rs. {item['target_price']:,.0f}"
    }


@app.get("/api/watchlist")
def api_get_watchlist():
    items = get_watchlist()
    return {"success": True, "watchlist": items}


@app.post("/api/launch")
def api_launch(req: LaunchRequest):
    url = req.url
    if not url or not url.startswith("http"):
        clean_title = (req.title or "product").replace(" ", "+")
        if "flipkart" in (req.site or "").lower():
            url = f"https://www.flipkart.com/search?q={clean_title}"
        else:
            url = f"https://www.amazon.in/s?k={clean_title}"

    opened = webbrowser.open(url)
    return {
        "success": True,
        "url": url,
        "opened": opened,
        "message": "Live browser window launched on your desktop!"
    }


@app.post("/api/search")
def api_search(req: SearchRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. AI Query Analysis
    query_info = understand_query(query)
    search_term = query_info.get("product_name", query)
    max_price = query_info.get("max_price")

    # 2. Live Scrape
    products = search_all(search_term, max_per_site=5)
    if max_price:
        filtered = [p for p in products if p.get("price", 999999) <= max_price]
        if filtered:
            products = filtered
        else:
            # If no items strictly under budget, pick items closest to budget
            products.sort(key=lambda p: abs(p.get("price", 999999) - max_price))

    if not products:
        # Ultimate fallback guarantee
        products = search_all(query, max_per_site=3)

    # 3. Deal Analysis
    winner = pick_best_deal(products, query)
    summary = summarize_comparison(products, winner)

    # 3.5 Head-to-Head Battle (Amazon vs. Flipkart)
    amazon_items = [p for p in products if p.get("site", "").lower() == "amazon"]
    flipkart_items = [p for p in products if p.get("site", "").lower() == "flipkart"]
    battle = None
    if amazon_items and flipkart_items:
        amz = amazon_items[0]
        flp = flipkart_items[0]
        diff = abs(amz.get("price", 0) - flp.get("price", 0))
        cheaper = "Amazon" if amz.get("price", 0) < flp.get("price", 0) else "Flipkart"
        battle = {
            "amazon": amz,
            "flipkart": flp,
            "price_diff": diff,
            "cheaper_store": cheaper,
            "verdict": f"{cheaper} is Rs. {diff:,.0f} cheaper!" if diff > 0 else "Both stores offer identical prices!"
        }

    # 4. Save to persistent memory
    remember_search(query, products, winner)
    stats = get_stats()
    stats["webcmd_connected"] = webcmd.is_available()

    return {
        "success": True,
        "query_info": {
            "original_query": query,
            "search_term": search_term,
            "max_price": max_price,
            "category": query_info.get("category", "General")
        },
        "products": products,
        "winner": winner,
        "summary": summary,
        "battle": battle,
        "stats": stats
    }


@app.get("/", response_class=HTMLResponse)
def index():
    html_file = Path(__file__).parent / "templates" / "index.html"
    if not html_file.exists():
        return HTMLResponse("<h1>Error: templates/index.html not found</h1>", status_code=404)
    with open(html_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("[SMARTCART] Localhost Web Server Starting...")
    print("   Open your browser at: http://localhost:3000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=3000)
