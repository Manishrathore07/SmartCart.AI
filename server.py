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

from brain import understand_query, pick_best_deal, summarize_comparison
from scraper import search_all
from memory import remember_search, get_stats
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


@app.get("/api/stats")
def api_stats():
    stats = get_stats()
    stats["webcmd_connected"] = webcmd.is_available()
    return stats


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

    if not products:
        return {
            "success": False,
            "message": "No products found. Please try another query.",
            "query_info": query_info,
            "products": []
        }

    # 3. Deal Analysis
    winner = pick_best_deal(products, query)
    summary = summarize_comparison(products, winner)

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
    print("   Open your browser at: http://localhost:8080")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8080)
