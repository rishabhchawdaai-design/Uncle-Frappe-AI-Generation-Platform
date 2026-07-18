#!/usr/bin/env python3
"""
Research MCP Stack — Data Collection Layer (20 Tools)
Unified CLI for crawling, scraping, and collecting web data.
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from wrappers.unified import UnifiedCollector
from mcp_adapters.adapter import MCPAdapter


async def cmd_collect(url: str, content_type: str = "static"):
    collector = UnifiedCollector()
    result = await collector.collect(url, content_type=content_type)
    print(f"\n  URL:        {result.url}")
    print(f"  Title:      {result.title or '(none)'}")
    print(f"  Collector:  {result.collector}")
    print(f"  Status:     {result.status}")
    print(f"  Duration:   {result.duration_ms}ms")
    print(f"  Content:    {len(result.content)} chars")
    if result.error:
        print(f"  Error:      {result.error}")
    if result.content:
        print(f"\n--- Content Preview (500 chars) ---\n{result.content[:500]}")
    return result


async def cmd_health():
    collector = UnifiedCollector()
    mcp = MCPAdapter()
    print("\n=== Python Collectors ===")
    tools = await collector.health_check_all()
    for name, info in tools.items():
        emoji = {"healthy": "✅", "needs_api_key": "🔑", "available": "✅"}.get(info.get("status", ""), "⚠️")
        print(f"  {emoji} {name:18s} [{info.get('status', '?')}]")
    print("\n=== MCP Servers ===")
    mcp_health = await mcp.health_check()
    for name, info in mcp_health.items():
        emoji = "✅" if info.get("status") == "available" else "⚠️"
        print(f"  {emoji} {name:18s} [{info.get('status', '?')}]")
        if "error" in info:
            print(f"     {info['error'][:80]}")
    print()


async def cmd_mcp_list():
    mcp = MCPAdapter()
    servers = mcp.list_servers()
    print("\n=== MCP Servers & Tools ===\n")
    for s in servers:
        print(f"  🔧 {s['name']} ({s['id']})")
        print(f"     {s['description']}")
        print(f"     Tools: {', '.join(s['tools'])}")
        print()


async def cmd_raipur(profile: str = "news"):
    from profiles.raipur import run_profile
    await run_profile(profile)


async def main():
    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("""
  Research MCP Stack — Data Collection Layer
  
  Usage:
    python main.py collect <url> [content_type]    Collect from a URL
    python main.py health                           Health check all tools
    python main.py mcp-list                         List MCP servers & tools
    python main.py raipur <profile>                 Run Raipur collection profile
    python main.py raipur-list                      List all Raipur profiles
    
  Content types: static, news, blog, government, academic, restaurant,
                 tourism, social, pdf, javascript, search
  
  Raipur profiles: government, news, restaurants, tourism, academic,
                    local_business, blogs, social
""")
    elif args[0] == "collect":
        url = args[1] if len(args) > 1 else "https://example.com"
        ct = args[2] if len(args) > 2 else "static"
        await cmd_collect(url, ct)
    elif args[0] == "health":
        await cmd_health()
    elif args[0] == "mcp-list":
        await cmd_mcp_list()
    elif args[0] == "raipur":
        profile = args[1] if len(args) > 1 else "news"
        await cmd_raipur(profile)
    elif args[0] == "raipur-list":
        from profiles.raipur import RAIPUR_PROFILES
        print("\n=== Raipur Collection Profiles ===\n")
        for name, p in RAIPUR_PROFILES.items():
            print(f"  📍 {name}")
            print(f"     Type: {p['content_type']} | URLs: {len(p['urls'])} | Schedule: {p['schedule']}")
            print(f"     Tools: {', '.join(p['preferred_tools'])}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
