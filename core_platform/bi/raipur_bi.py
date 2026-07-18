"""
Phase 17: Raipur Business Intelligence
Automated collection of restaurants, cafes, hotels, demographics,
real estate, competitor intel, menus, reviews, reports.
"""
import asyncio, json, logging, time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

@dataclass
class BICategory:
    name: str
    keywords: List[str]
    data_points: List[str]
    sources: List[str]
    collection_interval: str  # hourly, daily, weekly, monthly
    last_collected: str = ""

BICATEGORIES = {
    "restaurants": BICategory(
        name="restaurants",
        keywords=["restaurants Raipur", "best food Raipur", "top restaurants Chhattisgarh", "new restaurant Raipur"],
        data_points=["name", "rating", "reviews", "cuisine", "price_range", "address", "phone", "hours", "menu", "photos"],
        sources=["google_maps", "zomato", "swiggy", "justdial"],
        collection_interval="daily",
    ),
    "cafes": BICategory(
        name="cafes",
        keywords=["cafe Raipur", "coffee shop Raipur", "best cafe Chhattisgarh"],
        data_points=["name", "rating", "reviews", "specialties", "price_range", "wifi", "ambience"],
        sources=["google_maps", "zomato", "magicpin"],
        collection_interval="daily",
    ),
    "hotels": BICategory(
        name="hotels",
        keywords=["hotels Raipur", "budget hotels Raipur", "luxury hotels Chhattisgarh"],
        data_points=["name", "rating", "reviews", "star_rating", "price_range", "amenities", "photos"],
        sources=["google_maps", "tripadvisor", "justdial"],
        collection_interval="weekly",
    ),
    "cloud_kitchens": BICategory(
        name="cloud_kitchens",
        keywords=["cloud kitchen Raipur", "delivery kitchen Raipur", "online food Raipur"],
        data_points=["name", "rating", "delivery_time", "cuisine", "price_range", "platforms"],
        sources=["swiggy", "zomato"],
        collection_interval="daily",
    ),
    "commercial_property": BICategory(
        name="commercial_property",
        keywords=["commercial property Raipur", "office space Raipur", "shop for rent Raipur", "commercial rent Raipur"],
        data_points=["location", "area_sqft", "rent", "type", "amenities", "availability"],
        sources=["magicbricks", "99acres", "indiamart"],
        collection_interval="weekly",
    ),
    "demographics": BICategory(
        name="demographics",
        keywords=["Raipur population", "Raipur demographics", "Raipur census", "Chhattisgarh population"],
        data_points=["population", "growth_rate", "literacy_rate", "sex_ratio", "area", "density"],
        sources=["data_gov_in", "census"],
        collection_interval="monthly",
    ),
    "transport": BICategory(
        name="transport",
        keywords=["Raipur transport", "Raipur bus", "Raipur metro", "Raipur railway", "Raipur airport"],
        data_points=["routes", "fares", "timings", "capacity", "connectivity"],
        sources=["data_gov_in", "osm"],
        collection_interval="monthly",
    ),
    "government": BICategory(
        name="government",
        keywords=["Raipur government", "Chhattisgarh government notification", "Raipur municipal corporation"],
        data_points=["notifications", "tenders", "schemes", "permits", "regulations"],
        sources=["cg_gov", "smart_city", "raipur_mc"],
        collection_interval="daily",
    ),
    "news": BICategory(
        name="local_news",
        keywords=["Raipur news", "Raipur today", "Chhattisgarh news", "breaking news Raipur"],
        data_points=["headline", "source", "date", "category", "sentiment", "url"],
        sources=["google_search", "tavily", "serper"],
        collection_interval="hourly",
    ),
    "events": BICategory(
        name="events",
        keywords=["events Raipur", "events in Raipur today", "upcoming events Raipur"],
        data_points=["name", "date", "venue", "tickets", "organizer"],
        sources=["google_maps", "bookmyshow", "eventbrite"],
        collection_interval="daily",
    ),
    "startups": BICategory(
        name="startups",
        keywords=["startup Raipur", "IT company Raipur", "tech startup Chhattisgarh"],
        data_points=["name", "sector", "funding", "employees", "founder"],
        sources=["linkedin", "startup_india"],
        collection_interval="monthly",
    ),
    "competitor_pricing": BICategory(
        name="competitor_pricing",
        keywords=["restaurant prices Raipur", "food delivery pricing Raipur"],
        data_points=["item", "price", "restaurant", "platform", "discount"],
        sources=["zomato", "swiggy"],
        collection_interval="daily",
    ),
    "menus": BICategory(
        name="menus",
        keywords=["Raipur restaurant menu", "best biryani Raipur menu"],
        data_points=["restaurant", "items", "prices", "categories", "specials"],
        sources=["zomato", "swiggy"],
        collection_interval="weekly",
    ),
    "reviews": BICategory(
        name="reviews",
        keywords=["Raipur restaurant reviews", "best food reviews Raipur"],
        data_points=["restaurant", "reviewer", "rating", "text", "date", "sentiment"],
        sources=["google_maps", "zomato", "tripadvisor"],
        collection_interval="daily",
    ),
    "food_trends": BICategory(
        name="food_trends",
        keywords=["food trends Raipur", "trending food Chhattisgarh", "popular dishes Raipur"],
        data_points=["trend", "category", "growth", "seasonality"],
        sources=["google_trends", "social_media"],
        collection_interval="weekly",
    ),
    "expansion_opportunities": BICategory(
        name="expansion_opportunities",
        keywords=["new business Raipur", "expansion opportunity Chhattisgarh", "untapped market Raipur"],
        data_points=["location", "sector", "demand", "competition", "potential"],
        sources=["google_search", "data_gov_in"],
        collection_interval="monthly",
    ),
}


class RaipurBICollector:
    """Production Raipur Business Intelligence collector."""

    RAIPUR_BOUNDS = {"lat_min": 21.15, "lat_max": 21.40, "lng_min": 81.45, "lng_max": 81.85}

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._output_dir = Path(self.config.get("output_dir", "./data/raipur_bi"))
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._session: Optional[httpx.AsyncClient] = None
        self._collected: Dict[str, List[Dict]] = {}

    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=30, follow_redirects=True,
                headers={"User-Agent": "ResearchMCPStack/1.0"})
        return self._session

    async def collect_category(self, category_name: str, max_results: int = 20) -> Dict[str, Any]:
        cat = BICATEGORIES.get(category_name)
        if not cat:
            return {"error": f"Unknown category: {category_name}"}

        logger.info(f"Collecting {category_name}: {len(cat.keywords)} keywords")
        session = await self._get_session()
        results = []

        for keyword in cat.keywords[:3]:
            try:
                # Google search via Serper API (free tier) or direct
                serper_key = self.config.get("serper_api_key", "")
                tavily_key = self.config.get("tavily_api_key", "")

                if serper_key:
                    r = await session.post("https://google.serper.dev/search",
                        json={"q": keyword, "num": 5},
                        headers={"X-API-KEY": serper_key})
                    data = r.json()
                    organic = data.get("organic", [])
                    for item in organic[:5]:
                        results.append({
                            "keyword": keyword, "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""), "url": item.get("link", ""),
                            "source": "serper", "collected_at": datetime.now().isoformat(),
                        })
                elif tavily_key:
                    r = await session.post("https://api.tavily.com/search",
                        json={"api_key": tavily_key, "query": keyword, "max_results": 5})
                    data = r.json()
                    for item in data.get("results", [])[:5]:
                        results.append({
                            "keyword": keyword, "title": item.get("title", ""),
                            "snippet": item.get("content", "")[:200], "url": item.get("url", ""),
                            "source": "tavily", "collected_at": datetime.now().isoformat(),
                        })
                else:
                    # DuckDuckGo fallback
                    try:
                        from duckduckgo_search import DDGS
                        with DDGS() as ddgs:
                            ddg_results = list(ddgs.text(keyword, max_results=5))
                        for item in ddg_results[:5]:
                            results.append({
                                "keyword": keyword, "title": item.get("title", ""),
                                "snippet": item.get("body", "")[:200], "url": item.get("href", ""),
                                "source": "duckduckgo", "collected_at": datetime.now().isoformat(),
                            })
                    except ImportError:
                        pass

            except Exception as e:
                logger.warning(f"Error collecting {keyword}: {e}")

        self._collected[category_name] = results
        cat.last_collected = datetime.now().isoformat()

        # Save to file
        output_file = self._output_dir / f"{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.write_text(json.dumps({
            "category": category_name,
            "total_results": len(results),
            "keywords_used": cat.keywords[:3],
            "results": results,
        }, indent=2))

        return {"category": category_name, "collected": len(results), "file": str(output_file)}

    async def collect_all(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        targets = categories or list(BICATEGORIES.keys())
        results = {}
        for cat_name in targets:
            try:
                results[cat_name] = await self.collect_category(cat_name)
                await asyncio.sleep(2)  # Rate limiting between categories
            except Exception as e:
                results[cat_name] = {"error": str(e)}
        return results

    def generate_report(self) -> Dict[str, Any]:
        report = {
            "generated_at": datetime.now().isoformat(),
            "categories": {},
            "total_collected": 0,
        }
        for name, items in self._collected.items():
            report["categories"][name] = {
                "count": len(items),
                "interval": BICATEGORIES[name].collection_interval,
                "data_points": BICATEGORIES[name].data_points,
            }
            report["total_collected"] += len(items)
        return report

    async def close(self):
        if self._session:
            await self._session.aclose()
