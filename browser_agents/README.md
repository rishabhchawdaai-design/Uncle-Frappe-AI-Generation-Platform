# Research MCP Stack — Section 2: Internet & Browser Agents (20 Tools)

A comprehensive browser automation layer integrating 20 browser agents, AI-powered tools, and anti-detection frameworks into a single orchestrated system. Covers full browser automation, login flows, infinite scrolling, screenshots, PDFs, CAPTCHA handling, session persistence, and human-like browsing.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                 UnifiedBrowserAgent Orchestrator                 │
│         (capability routing · task matching · fallback)          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIER 1 — Core Browsers (10)          TIER 2 — Extended (10)    │
│  ┌──────────────────────┐              ┌──────────────────────┐  │
│  │ Playwright           │              │ AgentReach           │  │
│  │ Puppeteer            │              │ Helium               │  │
│  │ Selenium             │              │ BrowserPilot         │  │
│  │ Browserless          │              │ Chromium Remote      │  │
│  │ Camoufox             │              │ Open Operator        │  │
│  │ Steel Browser        │              │ AutoGen Browser      │  │
│  │ Browser Use          │              │ LangGraph Browser    │  │
│  │ Skyvern              │              │ CrewAI Browser       │  │
│  │ Stagehand            │              │                      │  │
│  │ Vision Browser       │              │                      │  │
│  └──────────────────────┘              └──────────────────────┘  │
│                                                                  │
│  SPECIALIZED                                                    │
│  ┌──────────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ OpenHands            │  │ OmniParser   │  │ 15 Capabilities│  │
│  │ (AI engineer)        │  │ (vision UI)  │  │ (mixins)      │  │
│  └──────────────────────┘  └──────────────┘  └───────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│  Docker Services: Selenium · Browserless · Skyvern · Steel      │
│  OmniParser · OpenHands · Stagehand · Chrome Debug              │
│  MCP Adapters · Capability Modules · Health Checks              │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Navigate to any URL
python main.py navigate https://example.com

# Login automation
python main.py login https://site.com user pass

# Screenshot
python main.py screenshot https://example.com

# Infinite scroll + extract
python main.py scroll https://example.com

# CAPTCHA detection
python main.py captcha https://example.com

# Health check
python main.py health

# List all 20 agents
python main.py list
```

## The 20 Browser Agents

### Tier 1 — Core Browsers (10)

| # | Agent | Type | Docker? | Key Capabilities |
|---|-------|------|---------|-----------------|
| 1 | **Browser Use** | AI agent | — | AI-driven browsing, form fill, multi-step |
| 2 | **Open Operator** | Browser | — | Login, cookies, session, screenshot |
| 3 | **OpenHands** | AI engineer | ✅ | Full browser + code execution |
| 4 | **Stagehand** | AI browser | ✅ | Structured extraction, screenshot |
| 5 | **Playwright** | Framework | — | **15/15 capabilities** — most complete |
| 6 | **Puppeteer** | CDP | — | Chrome DevTools, PDF, recording |
| 7 | **Browserless** | Cloud | ✅ | Headless-as-a-service, PDF, multi-session |
| 8 | **Steel Browser** | Anti-detect | ✅ | Stealth, proxy, session persistence |
| 9 | **Camoufox** | Anti-fingerprint | — | Firefox anti-fingerprint, stealth |
| 10 | **Selenium** | Grid | ✅ | **15/15 capabilities** — grid scaling |
| 11 | **Skyvern** | AI workflow | ✅ | Complex forms, CAPTCHA, human-like |
| 12 | **OmniParser** | Vision UI | ✅ | Screenshot → element parsing |
| 13 | **Vision Browser** | AI vision | — | GPT-4o screenshot analysis |

### Tier 2 — Extended (7)

| # | Agent | Type | Docker? | Key Capabilities |
|---|-------|------|---------|-----------------|
| 14 | **AgentReach** | Agent | — | Structured extraction, auto-retry |
| 15 | **Helium** | API wrapper | — | Simplified Python API |
| 16 | **BrowserPilot** | NL browser | — | Natural language commands |
| 17 | **Chromium Remote** | CDP | ✅ | Connect to existing Chrome |
| 18 | **AutoGen Browser** | AI agent | — | Microsoft AutoGen integration |
| 19 | **LangGraph Browser** | AI agent | — | LangChain graph workflows |
| 20 | **CrewAI Browser** | AI agent | — | Multi-agent crew tasks |

## 15 Capability Modules

Reusable capability mixins in `capabilities/`:

| # | Capability | Description | Agents |
|---|-----------|-------------|--------|
| 1 | **Login** | Auto-detect forms, fill credentials, submit | 10 agents |
| 2 | **Scrolling** | Infinite scroll, scroll-to-element, progress | 8 agents |
| 3 | **Screenshot** | Full page, viewport, element-level | 12 agents |
| 4 | **PDF Download** | Page → PDF generation | 4 agents |
| 5 | **CAPTCHA Detection** | Detect reCAPTCHA, hCAPTCHA, Turnstile | 6 agents |
| 6 | **Session Persistence** | Save/load sessions across runs | 5 agents |
| 7 | **Cookie Management** | Export, import, clear, query | 5 agents |
| 8 | **File Downloads** | Download with auto-rename | 3 agents |
| 9 | **Human-like Browsing** | Random delays, mouse movements, typing | 6 agents |
| 10 | **Parallel Browsing** | Concurrent multi-tab/URL | 3 agents |
| 11 | **Browser Recording** | Record + replay sessions | 3 agents |
| 12 | **Structured Extraction** | CSS selectors → JSON | 8 agents |
| 13 | **Auto Retry** | Exponential backoff retries | 5 agents |
| 14 | **Health Monitoring** | Browser process monitoring | 2 agents |
| 15 | **Stealth Mode** | Anti-detection, fingerprint avoidance | 3 agents |

## Task Routing

The `UnifiedBrowserAgent` routes tasks to the best agent:

| Task Type | Primary Agents | Use Case |
|-----------|---------------|----------|
| `simple_fetch` | Playwright, Puppeteer, Selenium | Basic page loading |
| `login_form` | Playwright, Selenium, Browser Use, Skyvern | Login flows |
| `infinite_scroll` | Playwright, Selenium, Helium | Long pages |
| `screenshot_capture` | Playwright, Vision, OmniParser | Visual capture |
| `pdf_generation` | Playwright, Puppeteer, Browserless | PDF export |
| `captcha_solve` | Vision Browser, Skyvern, Browser Use | Bot detection |
| `multi_step_form` | Skyvern, Playwright, AutoGen | Complex workflows |
| `structured_data` | Stagehand, Playwright, Skyvern | Data extraction |
| `stealth_scraping` | Camoufox, Steel, Chromium Remote | Anti-detection |
| `ai_guided` | Browser Use, AutoGen, LangGraph, CrewAI | AI-navigated |
| `parallel_browse` | Playwright, Browserless, Selenium | Multi-URL |
| `session_resume` | Playwright, Selenium, Steel | Persist state |

## Docker Services

```bash
docker compose -f docker/docker-compose.yml up -d

# Services:
#   selenium-hub       — Selenium Grid Hub        (port 4444)
#   selenium-chrome    — Chrome Node              (port auto)
#   selenium-firefox   — Firefox Node             (port auto)
#   browserless        — Browserless Chromium     (port 3000)
#   skyvern            — Skyvern AI Browser       (port 8080)
#   steel              — Steel Anti-detect        (port 3001)
#   openhands          — OpenHands AI Engineer    (port 3000)
#   omniparser         — OmniParser Vision UI     (port 8081)
#   chrome-debug       — Chrome Remote Debug      (port 9222)
#   stagehand          — Stagehand AI Browser     (port 7777)
#   gateway            — Nginx reverse proxy      (port 8889)
```

## Python Usage

```python
from browser_agents.unified import UnifiedBrowserAgent

ua = UnifiedBrowserAgent()

# Navigate
result = await ua.navigate("https://example.com", task_type="simple_fetch")

# Login
result = await ua.login("https://site.com", {"username": "u", "password": "p"})

# Screenshot
result = await ua.take_screenshot("https://example.com", full_page=True)

# Infinite scroll
result = await ua.scroll_and_extract("https://example.com")

# CAPTCHA check
result = await ua.detect_captcha("https://example.com")

# Batch
results = await ua.batch_navigate(urls, concurrency=5)

# Specific agent
from wrappers import AGENT_REGISTRY
agent = AGENT_REGISTRY["playwright"]()
result = await agent.navigate("https://example.com")
```

## Project Structure

```
browser_agents/
├── main.py                        # CLI entry point
├── unified.py                     # UnifiedBrowserAgent orchestrator
├── wrappers/                      # 20 agent wrappers
│   ├── base.py                    # BaseBrowserAgent + BrowserResult
│   ├── __init__.py                # Registry
│   ├── 01_browser_use.py          # 1.  Browser Use
│   ├── 02_agentreach.py           # 2.  AgentReach
│   ├── 03_open_operator.py        # 3.  Open Operator
│   ├── 04_openhands.py            # 4.  OpenHands
│   ├── 05_stagehand.py            # 5.  Stagehand
│   ├── 06_playwright.py           # 6.  Playwright
│   ├── 07_puppeteer.py            # 7.  Puppeteer
│   ├── 08_chromium_remote.py      # 8.  Chromium Remote
│   ├── 09_browserless.py          # 9.  Browserless
│   ├── 10_steel.py                # 10. Steel Browser
│   ├── 11_camoufox.py             # 11. Camoufox
│   ├── 12_selenium.py             # 12. Selenium
│   ├── 13_helium.py               # 13. Helium
│   ├── 14_browserpilot.py         # 14. BrowserPilot
│   ├── 15_autogen_browser.py      # 15. AutoGen Browser
│   ├── 16_langgraph_browser.py    # 16. LangGraph Browser
│   ├── 17_crewai_browser.py       # 17. CrewAI Browser
│   ├── 18_skyvern.py              # 18. Skyvern
│   ├── 19_omniparser.py           # 19. OmniParser
│   └── 20_vision_browser.py       # 20. Vision Browser
├── capabilities/                  # 15 reusable capability modules
│   └── browser_capabilities.py    # Login, scroll, screenshot, etc.
├── docker/                        # Docker Compose for browser services
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── Dockerfile.stagehand
├── health/
│   └── health.py                  # Health check system
├── profiles/                      # Pre-configured task profiles
└── README.md
```

## Agent Comparison Matrix

| Capability | Playwright | Selenium | Puppeteer | Browser Use | Skyvern | Camoufox | Steel | Vision |
|-----------|:----------:|:--------:|:---------:|:-----------:|:-------:|:--------:|:-----:|:------:|
| Login | ✅ | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ |
| Scrolling | ✅ | ✅ | ✅ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ |
| Screenshot | ✅ | ✅ | ✅ | ⚪ | ✅ | ✅ | ✅ | ✅ |
| PDF | ✅ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| CAPTCHA | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ✅ |
| Session | ✅ | ✅ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ⚪ |
| Cookies | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ |
| Downloads | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| Human-like | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ |
| Parallel | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| Recording | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| Extraction | ✅ | ✅ | ⚪ | ✅ | ✅ | ⚪ | ⚪ | ✅ |
| Stealth | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ⚪ |
| Multi-tab | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| Proxy | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ |
