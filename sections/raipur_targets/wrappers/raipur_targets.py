"""Section 10: Raipur Research Targets — All 20 categories + composite BI."""
import asyncio, time, json
from datetime import datetime
from sections.base import BaseTool, ToolResult, ToolCategory

RAIPUR_QUERIES = {
    "restaurants": {
        "keywords": ["restaurants Raipur", "best food Raipur", "non-veg Raipur", "veg restaurants Raipur", "thali Raipur"],
        "sources": ["zomato", "swiggy", "google_maps", "tripadvisor", "justdial"],
        "search_engines": ["google_pse", "exa", "tavily"],
        "schedule": "daily",
    },
    "cafes": {
        "keywords": ["cafes Raipur", "coffee shops Raipur", "best cafe Raipur", "cafe near me Raipur"],
        "sources": ["zomato", "google_maps", "foursquare", "magicpin"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "daily",
    },
    "hotels": {
        "keywords": ["hotels Raipur", "budget hotels Raipur", "luxury hotels Raipur", "OYO Raipur", "Airbnb Raipur"],
        "sources": ["tripadvisor", "google_maps", "booking_com"],
        "search_engines": ["google_pse", "exa", "tavily"],
        "schedule": "daily",
    },
    "cloud_kitchens": {
        "keywords": ["cloud kitchen Raipur", "delivery only Raipur", "kitchen only Raipur", "online food Raipur"],
        "sources": ["swiggy", "zomato", "google_maps"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "weekly",
    },
    "bakeries": {
        "keywords": ["bakeries Raipur", "cake shop Raipur", "bakery Raipur", "pastry shop Raipur"],
        "sources": ["zomato", "google_maps", "justdial", "magicpin"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "weekly",
    },
    "food_trucks": {
        "keywords": ["food truck Raipur", "food cart Raipur", "street food truck Raipur"],
        "sources": ["google_maps", "instagram", "zomato", "justdial"],
        "search_engines": ["google_pse", "x"],
        "schedule": "weekly",
    },
    "street_food": {
        "keywords": ["street food Raipur", "chaat Raipur", "golgappa Raipur", "samosa Raipur", "famous food Raipur"],
        "sources": ["google_maps", "tripadvisor", "youtube", "instagram"],
        "search_engines": ["google_pse", "exa", "tavily"],
        "schedule": "weekly",
    },
    "shopping_malls": {
        "keywords": ["shopping mall Raipur", "mall near me Raipur", "best malls Raipur"],
        "sources": ["google_maps", "justdial", "tripadvisor"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "monthly",
    },
    "markets": {
        "keywords": ["market Raipur", "bazaar Raipur", "local market Raipur", "shopping area Raipur", "City Centre Raipur"],
        "sources": ["google_maps", "justdial", "osm"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "monthly",
    },
    "colleges": {
        "keywords": ["colleges Raipur", "engineering college Raipur", "medical college Raipur", "university Raipur"],
        "sources": ["google_maps", "justdial", "indiamart"],
        "search_engines": ["google_pse", "exa", "openalex"],
        "schedule": "monthly",
    },
    "schools": {
        "keywords": ["schools Raipur", "best school Raipur", "CBSE school Raipur", "ICSE school Raipur"],
        "sources": ["google_maps", "justdial", "sulekha"],
        "search_engines": ["google_pse"],
        "schedule": "monthly",
    },
    "hospitals": {
        "keywords": ["hospitals Raipur", "best hospital Raipur", "government hospital Raipur", "private hospital Raipur", "AIIMS Raipur"],
        "sources": ["google_maps", "justdial", "practo"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "weekly",
    },
    "tourist_places": {
        "keywords": ["tourist places Raipur", "things to do Raipur", "Raipur sightseeing", "Ramakrishna Ashram Raipur", "Purkhouti Muktangan"],
        "sources": ["tripadvisor", "google_maps", "youtube", "instagram"],
        "search_engines": ["google_pse", "exa", "tavily"],
        "schedule": "monthly",
    },
    "events": {
        "keywords": ["events Raipur", "upcoming events Raipur", "events in Raipur today", "what's on Raipur"],
        "sources": ["google_maps", "instagram", "facebook", "bookmyshow"],
        "search_engines": ["google_pse", "x", "tavily"],
        "schedule": "daily",
    },
    "festivals": {
        "keywords": ["Raipur festival", "festivals Chhattisgarh", "Rajim fair", "Chhath Puja Raipur", "Dussehra Raipur"],
        "sources": ["youtube", "instagram", "medium", "substack"],
        "search_engines": ["google_pse", "exa", "tavily"],
        "schedule": "monthly",
    },
    "startups": {
        "keywords": ["startup Raipur", "startup India Raipur", "tech startup Chhattisgarh", "IT startup Raipur"],
        "sources": ["startup_india", "linkedin", "angel_list", "yourstory"],
        "search_engines": ["google_pse", "exa", "tavily"],
        "schedule": "monthly",
    },
    "it_companies": {
        "keywords": ["IT company Raipur", "software company Raipur", "IT park Raipur", "MIDC Raipur"],
        "sources": ["linkedin", "indiamart", "justdial", "naukri"],
        "search_engines": ["google_pse", "exa"],
        "schedule": "monthly",
    },
    "government_offices": {
        "keywords": ["government office Raipur", "collector office Raipur", "SDM Raipur", "court Raipur"],
        "sources": ["cg_gov", "data_gov_in", "justdial"],
        "search_engines": ["google_pse"],
        "schedule": "monthly",
    },
    "local_news": {
        "keywords": ["Raipur news", "Raipur today", "Chhattisgarh news", "breaking news Raipur", "समाचार रायपुर"],
        "sources": ["reddit", "x", "medium", "substack"],
        "search_engines": ["google_pse", "tavily", "exa", "serper"],
        "schedule": "hourly",
    },
    "business_intelligence": {
        "keywords": ["Raipur economy", "Raipur demographics", "Raipur population", "Raipur real estate", "Raipur transport", "commercial property Raipur", "rental rates Raipur", "Raipur competitors", "pricing data Raipur", "Raipur footfall", "Raipur expansion opportunities"],
        "sources": ["data_gov_in", "indiamart", "magicbricks", "99acres", "linkedin"],
        "search_engines": ["google_pse", "exa", "tavily", "serper", "brave"],
        "schedule": "daily",
    },
}

class RaipurTargetCollector(BaseTool):
    name = "raipur_target"; category = ToolCategory.RAIPUR_TARGETS
    capabilities = ["targeted_collection", "multi_source", "scheduled", "raipur_focused"]

    def __init__(self, config=None):
        super().__init__(config)
        self.search_mcp=None
        self.raipur_data=None

    def _set_dependencies(self, search_registry, raipur_registry):
        self.search_mcp=search_registry
        self.raipur_data=raipur_registry

    async def search(self, query, **kw):
        s=time.time()
        target=kw.get("target","restaurants")
        profile=RAIPUR_QUERIES.get(target)
        if not profile:
            return ToolResult(source=query,status="error",error=f"Unknown target: {target}. Available: {list(RAIPUR_QUERIES.keys())}",tool=self.name,duration_ms=self._timing(s))

        all_results={}
        for keyword in profile["keywords"]:
            all_results[keyword]=[]

        if self.search_mcp:
            for eng_name in profile["search_engines"][:2]:
                eng=self.search_mcp.get(eng_name)
                if eng:
                    for kw_text in profile["keywords"][:2]:
                        try:
                            result=await eng.search(kw_text,**kw)
                            all_results[kw_text].append({"engine":eng_name,"status":result.status,"data":result.raw[:2000] if result.raw else ""})
                        except: pass

        total_results=sum(len(v) for v in all_results.values())
        return ToolResult(
            source=query,
            data={"target":target,"profile":profile,"results":{k:v for k,v in all_results.items()},"total_results":total_results,"schedule":profile["schedule"]},
            tool=self.name,duration_ms=self._timing(s))

class RaipurCompositeBI(BaseTool):
    name = "raipur_bi"; category = ToolCategory.RAIPUR_TARGETS
    capabilities = ["composite", "all_targets", "business_intelligence", "dashboard"]
    async def search(self, query, **kw):
        s=time.time()
        collector=RaipurTargetCollector()
        results={}
        for target in RAIPUR_QUERIES:
            try:
                result=await collector.search(query,target=target,**kw)
                results[target]={"status":result.status,"data":result.data if hasattr(result,"data") else None}
            except: results[target]={"status":"error"}
        success=sum(1 for r in results.values() if r["status"]=="success")
        return ToolResult(source=query,data={"targets":results,"success":success,"total":len(results),"timestamp":datetime.now().isoformat()},tool=self.name,duration_ms=self._timing(s))

RAIPUR_TARGETS_REGISTRY={
    "restaurants": RaipurTargetCollector, "cafes": RaipurTargetCollector,
    "hotels": RaipurTargetCollector, "cloud_kitchens": RaipurTargetCollector,
    "bakeries": RaipurTargetCollector, "food_trucks": RaipurTargetCollector,
    "street_food": RaipurTargetCollector, "shopping_malls": RaipurTargetCollector,
    "markets": RaipurTargetCollector, "colleges": RaipurTargetCollector,
    "schools": RaipurTargetCollector, "hospitals": RaipurTargetCollector,
    "tourist_places": RaipurTargetCollector, "events": RaipurTargetCollector,
    "festivals": RaipurTargetCollector, "startups": RaipurTargetCollector,
    "it_companies": RaipurTargetCollector, "government_offices": RaipurTargetCollector,
    "local_news": RaipurTargetCollector, "business_intelligence": RaipurTargetCollector,
    "bi_composite": RaipurCompositeBI,
}
