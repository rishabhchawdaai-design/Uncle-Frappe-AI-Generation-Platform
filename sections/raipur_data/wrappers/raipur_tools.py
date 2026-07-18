"""Section 4: Local Raipur Data Sources — All 20 tools."""
import asyncio, time, json, os
from sections.base import BaseTool, ToolResult, ToolCategory

class GoogleMapsSource(BaseTool):
    name = "google_maps"; category = ToolCategory.RAIPUR_DATA; requires_api_key = True
    capabilities = ["places", "geocoding", "directions", "reviews", "photos"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            params={"input":f"{query} Raipur","inputtype":"textquery","fields":"name,rating,formatted_address,types,geometry","key":self._get_api_key("GOOGLE_MAPS_API_KEY")}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://maps.googleapis.com/maps/api/place/findplacefromtext/json",params=params)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class OpenStreetMapSource(BaseTool):
    name = "osm"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["nominatim", "overpass", "geocoding", "POI"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,headers={"User-Agent":"ResearchMCPStack/1.0"}) as c:
                r=await c.get("https://nominatim.openstreetmap.org/search",params={"q":f"{query} Raipur","format":"json","limit":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MapboxSource(BaseTool):
    name = "mapbox"; category = ToolCategory.RAIPUR_DATA; requires_api_key = True
    capabilities = ["geocoding", "static_maps", "directions", "matrix"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            token=self._get_api_key("MAPBOX_API_TOKEN")
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json",params={"access_token":token,"bbox":"81.5,21.15,81.85,21.4","limit":kw.get("num",5)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class FoursquareSource(BaseTool):
    name = "foursquare"; category = ToolCategory.RAIPUR_DATA; requires_api_key = True
    capabilities = ["venues", "tips", "photos", "categories"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":self._get_api_key("FOURSQUARE_API_KEY"),"Accept":"application/json"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.foursquare.com/v3/places/search",params={"query":query,"near":"Raipur, India","limit":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class YelpSource(BaseTool):
    name = "yelp"; category = ToolCategory.RAIPUR_DATA; requires_api_key = True
    capabilities = ["business_search", "reviews", "categories", "autocomplete"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bearer {self._get_api_key('YELP_API_KEY')}"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.yelp.com/v3/businesses/search",params={"term":query,"location":"Raipur, India","limit":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class TripAdvisorSource(BaseTool):
    name = "tripadvisor"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["locations", "reviews", "attractions", "restaurants"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.tripadvisor.com/TypeaheadJson",params={"action":"API", "typeahead_query": f"{query} Raipur"})
                return ToolResult(source=query,raw=r.text,tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ZomatoSource(BaseTool):
    name = "zomato"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["restaurants", "reviews", "menu", "delivery"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"user-key":self._get_api_key("ZOMATO_API_KEY")} if self._get_api_key("ZOMATO_API_KEY") else {}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://developers.zomato.com/api/v2.1/search",params={"q":f"{query} Raipur","city_id":"12"},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SwiggySource(BaseTool):
    name = "swiggy"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["restaurants", "delivery", "menus", "offers"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,headers={"User-Agent":"Mozilla/5.0"}) as c:
                r=await c.get("https://www.swiggy.com/dapi/restaurants/search/v3",params={"str":f"{query} Raipur","trackingId":None})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MagicpinSource(BaseTool):
    name = "magicpin"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["local_deals", "restaurants", "offers", "cashback"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://magicpin.in/api/search",params={"query":f"{query} Raipur","lat":21.25,"lng":81.63})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class JustdialSource(BaseTool):
    name = "justdial"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["business_directory", "reviews", "contact", "categories"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
                r=await c.get(f"https://www.justdial.com/Raipur/{query.replace(' ','-')}")
                return ToolResult(source=query,raw=r.text[:5000],metadata={"status":r.status_code},tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class IndiaMARTSource(BaseTool):
    name = "indiamart"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["suppliers", "products", "business_directory"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://dir.indiamart.com/impcat/search.mp",params={"q":f"{query} Raipur"})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SulekhaSource(BaseTool):
    name = "sulekha"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["local_services", "businesses", "professionals"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://www.sulekha.com/{query.lower().replace(' ','-')}/raipur")
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class YellowPagesSource(BaseTool):
    name = "yellowpages_in"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["business_directory", "contact", "categories"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://www.yellowpages.co.in/search/{query.lower().replace(' ','+')}_in_raipur")
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class CGGovPortal(BaseTool):
    name = "cg_gov"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["government", "schemes", "notices", "departments"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
                r=await c.get("https://cgstate.gov.in/",headers={"User-Agent":"Mozilla/5.0"})
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class RaipurSmartCity(BaseTool):
    name = "raipur_smart_city"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["smart_city", "projects", "citizen_services"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
                r=await c.get("https://raipursmartcity.in/")
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class RaipurMunicipalCorp(BaseTool):
    name = "raipur_mc"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["municipal", "tax", "permits", "services"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
                r=await c.get("https://raipurmunicipal.com/",headers={"User-Agent":"Mozilla/5.0"})
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MSMEPortal(BaseTool):
    name = "msme"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["msme", "registration", "subsidies", "clusters"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://udyamregistration.gov.in/")
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class StartupIndiaSource(BaseTool):
    name = "startup_india"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["startups", "recognition", "funding", "mentorship"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.startupindia.gov.in/search?query=Raipur")
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class GeMSource(BaseTool):
    name = "gem"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["government_procurement", "tenders", "products"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://gem.gov.in/search",params={"keyword":f"{query} Raipur"})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class DataGovInSource(BaseTool):
    name = "data_gov_in"; category = ToolCategory.RAIPUR_DATA
    capabilities = ["open_data", "datasets", "government_data", "APIs"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://data.gov.in/search",params={"query":f"{query} Raipur Chhattisgarh"})
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

RAIPUR_REGISTRY = {
    "google_maps": GoogleMapsSource, "osm": OpenStreetMapSource,
    "mapbox": MapboxSource, "foursquare": FoursquareSource,
    "yelp": YelpSource, "tripadvisor": TripAdvisorSource,
    "zomato": ZomatoSource, "swiggy": SwiggySource,
    "magicpin": MagicpinSource, "justdial": JustdialSource,
    "indiamart": IndiaMARTSource, "sulekha": SulekhaSource,
    "yellowpages": YellowPagesSource, "cg_gov": CGGovPortal,
    "smart_city": RaipurSmartCity, "raipur_mc": RaipurMunicipalCorp,
    "msme": MSMEPortal, "startup_india": StartupIndiaSource,
    "gem": GeMSource, "data_gov_in": DataGovInSource,
}
