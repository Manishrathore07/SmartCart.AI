"""
SmartCart Agent — Streamlit UI
The main app interface. Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Import our modules
from brain import understand_query, pick_best_deal, summarize_comparison
from scraper import search_all
from memory import remember_search, get_stats, track_price

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🛒 SmartCart Agent",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .product-card {
        background: white;
        border: 2px solid #eee;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .product-card:hover { border-color: #667eea; }
    .winner-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        margin: 1rem 0;
    }
    .amazon-badge {
        background: #FF9900;
        color: black;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .flipkart-badge {
        background: #2874F0;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .approval-box {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .stat-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar: User Profile ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Your Profile")
    st.caption("Saved for auto form-filling")

    user_name    = st.text_input("Full Name",    value=os.getenv("USER_NAME", ""))
    user_email   = st.text_input("Email",        value=os.getenv("USER_EMAIL", ""))
    user_phone   = st.text_input("Phone",        value=os.getenv("USER_PHONE", ""))
    user_address = st.text_input("Address",      value=os.getenv("USER_ADDRESS", ""))
    user_city    = st.text_input("City",         value=os.getenv("USER_CITY", ""))
    user_pincode = st.text_input("PIN Code",     value=os.getenv("USER_PINCODE", ""))

    user_profile = {
        "name": user_name, "email": user_email,
        "phone": user_phone, "address": user_address,
        "city": user_city, "pincode": user_pincode
    }

    st.divider()

    # Stats Panel
    st.markdown("## 📊 Agent Stats")
    stats = get_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Searches", stats["total_searches"])
    with col2:
        st.metric("₹ Saved", f"₹{stats['money_saved']:.0f}")

    if stats["learned_sites"]:
        st.success(f"🧠 Learned: {', '.join(stats['learned_sites'])}")

    st.divider()
    st.markdown("## 🔑 API Status")
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key != "your_free_gemini_api_key_here":
        st.success("✅ Gemini API Connected")
    else:
        st.error("❌ Add API key to .env file")
        st.caption("Get FREE key: [aistudio.google.com](https://aistudio.google.com/apikey)")


# ── Main Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛒 SmartCart Agent</h1>
    <p style="font-size:1.2rem; opacity:0.9">
        AI-powered price hunter for Amazon & Flipkart<br>
        <em>Tell me what you want. I'll find the cheapest price.</em>
    </p>
</div>
""", unsafe_allow_html=True)


# ── Search Input ──────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1])
with col_input:
    user_query = st.text_input(
        "What do you want to buy?",
        placeholder="e.g. wireless earbuds under 2000 rupees, Python book, laptop bag...",
        label_visibility="collapsed"
    )
with col_btn:
    search_btn = st.button("🔍 Hunt Deals!", use_container_width=True, type="primary")


# ── Example Queries ───────────────────────────────────────────────────────────
st.markdown("**Quick examples:**")
examples = [
    "wireless earbuds under ₹2000",
    "Python programming book",
    "USB-C charging cable",
    "laptop bag under ₹1500",
    "noise cancelling headphones"
]
cols = st.columns(len(examples))
for i, ex in enumerate(examples):
    with cols[i]:
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            user_query = ex
            search_btn = True


# ── Search Execution ──────────────────────────────────────────────────────────
if search_btn and user_query:
    st.divider()

    # Step 1: Understand query
    with st.status("🧠 Understanding your request...", expanded=True) as status:
        try:
            query_info = understand_query(user_query)
            st.write(f"**Product:** {query_info.get('product_name', user_query)}")
            st.write(f"**Category:** {query_info.get('category', 'general')}")
            max_price = query_info.get('max_price')
            if max_price:
                st.write(f"**Budget:** ₹{max_price:,}")
            keywords = query_info.get('keywords', [])
            search_term = query_info.get('product_name', user_query)
            status.update(label="✅ Query understood!", state="complete")
        except Exception as e:
            st.error(f"Gemini API error: {e}")
            st.info("💡 Make sure your GEMINI_API_KEY is set in the .env file")
            st.stop()

    # Step 2: Search both sites
    with st.status("🌐 Searching Amazon & Flipkart...", expanded=True) as status:
        st.write("🛒 Hitting Amazon India...")
        time.sleep(0.5)
        st.write("🛍️ Hitting Flipkart...")

        products = search_all(search_term, max_per_site=5)

        # Filter by max price if specified
        if max_price:
            products = [p for p in products if p.get("price", 999999) <= max_price]

        amazon_count   = sum(1 for p in products if p.get("site") == "amazon")
        flipkart_count = sum(1 for p in products if p.get("site") == "flipkart")

        st.write(f"Found **{len(products)} products** — Amazon: {amazon_count}, Flipkart: {flipkart_count}")
        status.update(label=f"✅ Found {len(products)} products!", state="complete")

    if not products:
        st.warning("😕 No products found. Try a different search term or check your internet connection.")
        st.stop()

    # Track prices in memory
    for p in products:
        track_price(p.get("title", ""), p.get("site", ""), p.get("price", 0))

    # Step 3: AI picks best deal
    with st.status("🤖 Gemini is picking the best deal...", expanded=True) as status:
        winner = pick_best_deal(products, user_query)
        summary = summarize_comparison(products, winner)
        status.update(label="✅ Best deal found!", state="complete")

    # Save to memory
    remember_search(user_query, products, winner)

    # ── Results Display ────────────────────────────────────────────────────────
    st.markdown("## 🏆 Best Deal Found!")

    winner_product = winner.get("winner_product", {})
    if winner_product:
        site = winner_product.get("site", "")
        badge = (
            '<span class="amazon-badge">AMAZON</span>'   if site == "amazon"
            else '<span class="flipkart-badge">FLIPKART</span>'
        )
        st.markdown(f"""
        <div class="winner-card">
            <h3>🥇 {winner_product.get('title', 'Best Deal')[:70]}</h3>
            <h2 style="margin:0">₹{winner_product.get('price', 0):,.0f}</h2>
            {badge}
            &nbsp;&nbsp;⭐ {winner_product.get('rating', 0):.1f}
            &nbsp;&nbsp;💬 {winner_product.get('review_count', 0):,} reviews
        </div>
        """, unsafe_allow_html=True)

        # AI Summary
        st.info(f"💡 **AI Says:** {summary}")

        if winner.get("warning"):
            st.warning(f"⚠️ {winner.get('warning')}")

    # ── All Products Table ─────────────────────────────────────────────────────
    st.markdown("## 📊 Price Comparison")

    tab1, tab2, tab3 = st.tabs(["📋 All Results", "🛒 Amazon Only", "🛍️ Flipkart Only"])

    def render_table(data: list):
        if not data:
            st.info("No products from this site for this search.")
            return
        df = pd.DataFrame(data)
        display_cols = ["title", "price", "original_price", "discount_pct", "rating", "review_count", "in_stock", "site"]
        df = df[[c for c in display_cols if c in df.columns]]
        df.columns = ["Title", "Price (₹)", "Original (₹)", "Discount %", "Rating", "Reviews", "In Stock", "Site"]
        df["Title"] = df["Title"].str[:50] + "..."
        df = df.sort_values("Price (₹)")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab1:
        render_table(products)
    with tab2:
        render_table([p for p in products if p.get("site") == "amazon"])
    with tab3:
        render_table([p for p in products if p.get("site") == "flipkart"])

    # ── Human Approval Section ─────────────────────────────────────────────────
    st.markdown("## ⚠️ Human Approval Required")
    st.markdown("""
    <div class="approval-box">
        <h3>🔐 Review Before Proceeding</h3>
        <p>SmartCart Agent will <strong>open your browser</strong> and navigate to the product page.
        <strong>You control what happens next.</strong></p>
        <ul>
            <li>✅ Your saved profile will auto-fill the form</li>
            <li>✅ The browser stays visible — you can see everything</li>
            <li>✅ <strong>No purchase is made without YOUR final click</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if winner_product:
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            st.markdown(f"**Selected:** {winner_product.get('title', '')[:60]}...")
            st.markdown(f"**Price:** ₹{winner_product.get('price', 0):,.0f} on **{site.upper()}**")
        with col_b:
            st.markdown(f"**Shipping to:** {user_city or 'your location'}")
            st.markdown(f"**Your name:** {user_name or '(not set)'}")

        with col_c:
            go_to_site = st.button(
                "🛒 Open Product Page",
                type="primary",
                use_container_width=True,
                help="Opens the product in your browser"
            )

        if go_to_site:
            product_url = winner_product.get("url", "")
            if product_url:
                st.success(f"🌐 Opening: {product_url[:80]}...")
                # Open in default browser
                import webbrowser
                webbrowser.open(product_url)
                st.balloons()
                st.success("""
                ✅ **Product page opened in your browser!**
                
                The agent has done its job — found you the best deal.
                The form-filling automation requires running with Playwright 
                (see `form_filler.py` for the full browser automation).
                
                **You're in control of the final purchase!** 🎉
                """)
            else:
                st.error("No URL found for this product.")

    # ── Price History Chart ────────────────────────────────────────────────────
    st.markdown("## 📈 Search History")
    stats = get_stats()
    if stats["recent_searches"]:
        history_df = pd.DataFrame(stats["recent_searches"])
        if "query" in history_df.columns:
            st.dataframe(
                history_df[["query", "winner_site", "winner_price", "total_products_found"]].rename(
                    columns={
                        "query": "Search",
                        "winner_site": "Best Site",
                        "winner_price": "Best Price (₹)",
                        "total_products_found": "Products Found"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#888; padding:1rem">
    🤖 <strong>SmartCart Agent</strong> — Built for SLAB Hackathon 2026<br>
    Powered by <strong>Google Gemini (Free Tier)</strong> • Amazon India • Flipkart<br>
    <em>Explore once. Learn. Reuse. Save money.</em>
</div>
""", unsafe_allow_html=True)
