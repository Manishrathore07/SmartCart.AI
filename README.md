# 🛒 SmartCart AI — Autonomous Shopping Browser Agent

> **SLAB Hackathon 2026 — Browser Agents Track**  
> Powered by **@agentrhq/webcmd** & **Google Gemini 3.6 Flash**  
> *Autonomous price discovery, deal reasoning, and browser navigation across Amazon India & Flipkart with a mandatory Human Approval safeguard.*

---

## 🌟 Features

- **Cross-Store Discovery**: Live price comparison across Amazon.in and Flipkart.
- **Cognitive AI Brain**: Google Gemini 3.6 Flash dynamically extracts purchase intent, categories, and price constraints.
- **Smart Value Optimization**: Gemini scores items not just on price, but also seller rating, reviews, discount percentage, and delivery cost.
- **Webcmd Self-Learning Browser Infra**: Integrated with `@agentrhq/webcmd` CLI for persistent profile management and session execution.
- **Human Approval Safeguard**: Mandates user review before any purchase action—never automatically submits payments.
- **Modern Localhost Web UI**: Sleek glassmorphic dark interface with live 4-stage pipeline visualization, interactive price cards, and 1-click browser launching.
- **Persistent Memory**: Tracks total searches and lifetime rupees saved in `memory.json`.

---

## 🏗️ Architecture

```
User Query ("wireless mouse under 1000")
       │
       ▼
🧠 Gemini AI Intent Parsing (extracts keywords, budget constraints)
       │
       ▼
🌐 Multi-Store Live Scraping (Amazon India & Flipkart)
       │
       ▼
⚖️ Gemini Price-to-Value Engine (evaluates ratings, discounts, seller reliability)
       │
       ▼
🏆 AI Deal Winner Picked + Reasoning Generated
       │
       ▼
🔒 HUMAN APPROVAL SAFEGUARD (User reviews winning deal & price)
       │
       ▼
🚀 Live Browser Window / Tab Launched directly onto Product Page
       │
       ▼
💾 Persistent Memory Updated (tracks queries & cumulative savings)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 18+** (for `@agentrhq/webcmd`)
- Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/apikey))

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/smartcart-agent.git
cd smartcart-agent

# Install dependencies
py -3.12 -m pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and insert your Gemini API key:

```bash
copy .env.example .env
```

Inside `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
USER_NAME=Your Name
USER_PHONE=9876543210
USER_PINCODE=110001
```

---

## 💻 Running the Agent

### Option 1: Modern Web Dashboard (Recommended)

Start the local web application:

```bash
py -3.12 server.py
```

Then open your browser at:
👉 **[http://localhost:8080](http://localhost:8080)**

- Type any product search or click one of the quick chips.
- Watch the 4-stage AI pipeline execute in real-time.
- Click **"Launch Live Browser Window"** or **"View Deal"** to open the product directly in your browser.

---

### Option 2: Command Line Interface (CLI)

Run the autonomous agent directly from your terminal:

```bash
py -3.12 -u agent.py "wireless mouse under 1000"
```

Or for other items:
```bash
py -3.12 -u agent.py "running shoes under 2000"
py -3.12 -u agent.py "mechanical keyboard"
```

---

## 📁 Repository Structure

```
smartcart-agent/
├── server.py             # FastAPI localhost backend & API routes
├── templates/
│   └── index.html        # Modern Tailwind CSS / Lucide web dashboard
├── agent.py              # CLI runner for quick terminal execution
├── brain.py              # Gemini 3.6 Flash reasoning & query understanding
├── scraper.py            # Amazon.in & Flipkart scraping engine
├── webcmd_adapter.py     # @agentrhq/webcmd CLI integration bridge
├── form_filler.py        # Automated form navigation & human approval gate
├── memory.py             # Persistent search & savings memory
├── memory.json           # Tracked search sessions & metrics
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git exclusion rules (protects API keys)
└── README.md             # Project documentation
```

---

## 🏆 Hackathon Compliance & Safety

- **Human-in-the-Loop**: The agent guides the user to the best verified deal, prepares the page navigation, and defers final purchase confirmation to the human.
- **Privacy & Safety**: Credentials and API keys are stored locally in `.env` and excluded from source control.
- **Resilience**: Features automatic network failovers and realistic search fallbacks if external APIs experience transient blocks.

---

## 📄 License

MIT License — Built for the SLAB Hackathon 2026.
