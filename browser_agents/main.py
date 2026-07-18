#!/usr/bin/env python3
"""
Research MCP Stack — Section 2: Browser Agents (20 Tools)
Unified CLI for browser automation, AI agents, and web interaction.
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def cmd_navigate(url: str, agent: str = "unified"):
    from wrappers import AGENT_REGISTRY
    if agent == "unified":
        from unified import UnifiedBrowserAgent
        ua = UnifiedBrowserAgent()
        result = await ua.navigate(url)
    else:
        cls = AGENT_REGISTRY.get(agent)
        if not cls:
            print(f"Unknown agent: {agent}")
            return
        a = cls()
        result = await a.navigate(url)

    print(f"\n  URL:        {result.url}")
    print(f"  Title:      {result.title or '(none)'}")
    print(f"  Agent:      {result.agent}")
    print(f"  Status:     {result.status}")
    print(f"  Duration:   {result.duration_ms}ms")
    print(f"  Content:    {len(result.content)} chars")
    print(f"  Cookies:    {len(result.cookies)}")
    if result.screenshot:
        print(f"  Screenshot: {len(result.screenshot)} bytes")
    if result.error:
        print(f"  Error:      {result.error}")
    if result.content:
        print(f"\n--- Content Preview (500 chars) ---\n{result.content[:500]}")
    return result


async def cmd_login(url: str, username: str, password: str, agent: str = "unified"):
    from unified import UnifiedBrowserAgent
    ua = UnifiedBrowserAgent()
    result = await ua.login(url, {"username": username, "password": password})
    print(f"\n  Login:      {result.status}")
    print(f"  Agent:      {result.agent}")
    print(f"  Duration:   {result.duration_ms}ms")
    if result.error:
        print(f"  Error:      {result.error}")
    return result


async def cmd_screenshot(url: str):
    from unified import UnifiedBrowserAgent
    ua = UnifiedBrowserAgent()
    result = await ua.navigate(url, take_screenshot=True, full_page=True)
    if result.screenshot:
        path = f"output/screenshots/{url.replace('https://', '').replace('/', '_')[:60]}.png"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(result.screenshot)
        print(f"\n  Screenshot saved: {path} ({len(result.screenshot)} bytes)")
    else:
        print(f"\n  Screenshot failed: {result.error}")


async def cmd_scroll(url: str):
    from unified import UnifiedBrowserAgent
    ua = UnifiedBrowserAgent()
    result = await ua.scroll_and_extract(url)
    print(f"\n  URL:        {result.url}")
    print(f"  Content:    {len(result.content)} chars (after scrolling)")
    print(f"  Agent:      {result.agent}")
    return result


async def cmd_captcha(url: str):
    from unified import UnifiedBrowserAgent
    ua = UnifiedBrowserAgent()
    result = await ua.detect_captcha(url)
    detected = result.metadata.get("captcha_detected", False)
    print(f"\n  CAPTCHA:    {'🔴 DETECTED' if detected else '🟢 NOT FOUND'}")
    print(f"  URL:        {result.url}")
    if detected:
        details = result.metadata.get("captcha_details", "")
        print(f"  Details:    {details[:200]}")
    return result


async def cmd_health():
    from wrappers import AGENT_REGISTRY
    print("\n=== Browser Agents Health Check ===\n")
    results = {}
    for name, cls in AGENT_REGISTRY.items():
        try:
            agent = cls(config={})
            check = await asyncio.wait_for(agent.health_check(), timeout=3)
            status = check.get("status", "unknown")
            emoji = {"available": "✅", "healthy": "✅"}.get(status, "⚠️")
            caps = check.get("capabilities", [])
            print(f"  {emoji} {name:20s} [{status}]  caps={len(caps)}")
            results[name] = {"status": status, "capabilities": caps}
        except asyncio.TimeoutError:
            print(f"  ⏰ {name:20s} [timeout]")
        except Exception as e:
            print(f"  ❌ {name:20s} [error: {str(e)[:40]}]")
    print()


async def cmd_agents_list():
    from wrappers import AGENT_REGISTRY
    print("\n=== 20 Browser Agents ===\n")
    for name, cls in AGENT_REGISTRY.items():
        agent = cls(config={})
        caps = [c.value for c in agent.capabilities]
        tier = AGENT_INFO.get(name, {}).get("tier", "?")
        print(f"  T{tier}  {name:20s}  [{len(caps):2d} caps]  {', '.join(caps[:5])}{'...' if len(caps) > 5 else ''}")
    print()


AGENT_INFO = {
    "browser_use": {"tier": 1}, "agentreach": {"tier": 2},
    "open_operator": {"tier": 1}, "openhands": {"tier": 1},
    "stagehand": {"tier": 1}, "playwright": {"tier": 1},
    "puppeteer": {"tier": 1}, "chromium_remote": {"tier": 2},
    "browserless": {"tier": 1}, "steel": {"tier": 1},
    "camoufox": {"tier": 1}, "selenium": {"tier": 1},
    "helium": {"tier": 2}, "browserpilot": {"tier": 2},
    "autogen_browser": {"tier": 2}, "langgraph_browser": {"tier": 2},
    "crewai_browser": {"tier": 2}, "skyvern": {"tier": 1},
    "omniparser": {"tier": 1}, "vision_browser": {"tier": 1},
}


async def main():
    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("""
  Research MCP Stack — Browser Agents (20 Tools)
  
  Usage:
    python main.py navigate <url> [agent]       Navigate to URL
    python main.py login <url> <user> <pass>     Login automation
    python main.py screenshot <url>              Full-page screenshot
    python main.py scroll <url>                  Infinite scroll + extract
    python main.py captcha <url>                 CAPTCHA detection
    python main.py health                        Health check all agents
    python main.py list                          List all 20 agents
""")
    elif args[0] == "navigate":
        await cmd_navigate(args[1] if len(args) > 1 else "https://example.com",
                          agent=args[2] if len(args) > 2 else "unified")
    elif args[0] == "login":
        await cmd_login(args[1], args[2], args[3])
    elif args[0] == "screenshot":
        await cmd_screenshot(args[1] if len(args) > 1 else "https://example.com")
    elif args[0] == "scroll":
        await cmd_scroll(args[1] if len(args) > 1 else "https://example.com")
    elif args[0] == "captcha":
        await cmd_captcha(args[1] if len(args) > 1 else "https://example.com")
    elif args[0] == "health":
        await cmd_health()
    elif args[0] == "list":
        await cmd_agents_list()


if __name__ == "__main__":
    asyncio.run(main())
