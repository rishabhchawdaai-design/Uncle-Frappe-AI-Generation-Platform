#!/usr/bin/env python3
"""
Research MCP Stack — Sections 3-10 CLI
160 tools across Search, Raipur Data, Social, AI Research, OCR, KG, Validation, Targets
"""
import asyncio, sys, json
sys.path.insert(0, str(Path(__file__).parent.parent) if "/" in str(__file__) else ".")
from pathlib import Path
from sections.unified_orchestrator import UnifiedOrchestrator

async def cmd_search(query, category="search"):
    orch = UnifiedOrchestrator()
    result = await orch.search(query, category=category)
    print(f"\n  Query:    {result.source}")
    print(f"  Category: {result.category or category}")
    print(f"  Tool:     {result.tool}")
    print(f"  Status:   {result.status}")
    print(f"  Duration: {result.duration_ms}ms")
    if result.data:
        print(f"  Data:     {json.dumps(result.data, indent=2)[:500]}")
    if result.error:
        print(f"  Error:    {result.error}")

async def cmd_raipur(target):
    orch = UnifiedOrchestrator()
    result = await orch.raipur_research(target)
    print(f"\n  Target:   {target}")
    print(f"  Status:   {result.status}")
    print(f"  Tool:     {result.tool}")
    print(f"  Duration: {result.duration_ms}ms")
    if result.data:
        print(f"  Results:  {json.dumps(result.data, indent=2)[:800]}")

async def cmd_health():
    from sections.health_check import health_check_all
    await health_check_all()

async def cmd_stats():
    orch = UnifiedOrchestrator()
    stats = orch.get_stats()
    print(f"\n  Total Tools:  {stats['total']}")
    print(f"\n  By Category:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"    {cat:30s}  {count}")

async def cmd_targets():
    from sections.raipur_targets.wrappers.raipur_targets import RAIPUR_QUERIES
    print("\n  Raipur Research Targets:")
    for name, profile in RAIPUR_QUERIES.items():
        print(f"    {name:25s}  keywords={len(profile['keywords'])}  schedule={profile['schedule']}")
    print(f"\n  Total: {len(RAIPUR_QUERIES)} targets")

async def main():
    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("""
  Research MCP Stack — Sections 3-10 (160 tools)
  
  Usage:
    python sections/cli.py search <query> [category]     Search across tools
    python sections/cli.py raipur <target>               Raipur target research
    python sections/cli.py health                        Health check all 160 tools
    python sections/cli.py stats                         Tool statistics
    python sections/cli.py targets                       List Raipur targets
  
  Categories: search, local_business, news, social, government, academic,
              restaurants, document, image_ocr, graph, validation, ai_agent
  Targets: restaurants, cafes, hotels, cloud_kitchens, bakeries, food_trucks,
           street_food, shopping_malls, markets, colleges, schools, hospitals,
           tourist_places, events, festivals, startups, it_companies,
           government_offices, local_news, business_intelligence
""")
    elif args[0] == "search":
        await cmd_search(args[1] if len(args) > 1 else "Raipur", args[2] if len(args) > 2 else "search")
    elif args[0] == "raipur":
        await cmd_raipur(args[1] if len(args) > 1 else "restaurants")
    elif args[0] == "health":
        await cmd_health()
    elif args[0] == "stats":
        await cmd_stats()
    elif args[0] == "targets":
        await cmd_targets()

if __name__ == "__main__":
    asyncio.run(main())
