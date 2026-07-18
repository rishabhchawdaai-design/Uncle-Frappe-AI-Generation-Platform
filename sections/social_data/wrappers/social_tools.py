"""Section 5: Social Data — All 20 platforms."""
import asyncio, time, json, os
from sections.base import BaseTool, ToolResult, ToolCategory

class RedditSource(BaseTool):
    name = "reddit"; category = ToolCategory.SOCIAL
    mcp_server = "reddit-mcp"; capabilities = ["posts", "comments", "subreddits", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,headers={"User-Agent":"ResearchMCP/1.0"}) as c:
                r=await c.get(f"https://www.reddit.com/search.json",params={"q":f"{query} Raipur","limit":kw.get("num",10),"sort":kw.get("sort","relevance")})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class XSource(BaseTool):
    name = "x_twitter"; category = ToolCategory.SOCIAL; requires_api_key = True
    mcp_server = "twitter-mcp"; capabilities = ["posts", "search", "trends", "user_timeline"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bearer {self._get_api_key('TWITTER_BEARER_TOKEN')}"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.twitter.com/2/tweets/search/recent",params={"query":f"{query} Raipur lang:en","max_results":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class FacebookSource(BaseTool):
    name = "facebook"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["pages", "search", "posts", "reviews"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://graph.facebook.com/v18.0/search",params={"q":f"{query} Raipur","type":"page","access_token":self._get_api_key("FB_ACCESS_TOKEN")})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class InstagramSource(BaseTool):
    name = "instagram"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["posts", "hashtags", "location_tags", "user_profile"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://graph.instagram.com/v18.0/ig_hashtag_search",params={"q":f"{query} Raipur","access_token":self._get_api_key("IG_ACCESS_TOKEN")})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ThreadsSource(BaseTool):
    name = "threads"; category = ToolCategory.SOCIAL
    capabilities = ["posts", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://www.threads.net/search?q={query}+Raipur")
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class LinkedInSource(BaseTool):
    name = "linkedin"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["company", "people", "jobs", "posts"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bearer {self._get_api_key('LINKEDIN_ACCESS_TOKEN')}"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.linkedin.com/v2/search",params={"q":f"{query} Raipur","count":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class YouTubeSource(BaseTool):
    name = "youtube"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["videos", "channels", "playlists", "comments"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.googleapis.com/youtube/v3/search",params={"q":f"{query} Raipur","part":"snippet","maxResults":kw.get("num",10),"key":self._get_api_key("YOUTUBE_API_KEY")})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class TelegramSource(BaseTool):
    name = "telegram"; category = ToolCategory.SOCIAL
    capabilities = ["channels", "messages", "groups", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            token=self._get_api_key("TELEGRAM_BOT_TOKEN")
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://api.telegram.org/bot{token}/searchPublicChat",params={"query":query})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class DiscordSource(BaseTool):
    name = "discord"; category = ToolCategory.SOCIAL
    capabilities = ["servers", "messages", "bot_api"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://discord.com/api/v10/guilds/search",params={"query":f"Raipur {query}"},headers={"Authorization":f"Bot {self._get_api_key('DISCORD_BOT_TOKEN')}"})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PinterestSource(BaseTool):
    name = "pinterest"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["pins", "boards", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.pinterest.com/v5/search/pins",params={"query":f"{query} Raipur"},headers={"Authorization":f"Bearer {self._get_api_key('PINTEREST_TOKEN')}"})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class QuoraSource(BaseTool):
    name = "quora"; category = ToolCategory.SOCIAL
    capabilities = ["questions", "answers", "topics"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
                r=await c.get(f"https://www.quora.com/search?q={query}+Raipur")
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MediumSource(BaseTool):
    name = "medium"; category = ToolCategory.SOCIAL
    capabilities = ["articles", "publications", "authors"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://medium.com/search",params={"q":f"{query} Raipur"})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SubstackSource(BaseTool):
    name = "substack"; category = ToolCategory.SOCIAL
    capabilities = ["newsletters", "articles", "authors"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://substack.com/api/v1/search/public",params={"query":f"{query} Raipur"})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class TumblrSource(BaseTool):
    name = "tumblr"; category = ToolCategory.SOCIAL
    capabilities = ["posts", "blogs", "tags"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://api.tumblr.com/v2/tag/{query}",params={"api_key":self._get_api_key("TUMBLR_API_KEY")})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class FlickrSource(BaseTool):
    name = "flickr"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["photos", "albums", "geotags", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.flickr.com/services/rest/",params={"method":"flickr.photos.search","api_key":self._get_api_key("FLICKR_API_KEY"),"text":f"{query} Raipur","format":"json","nojsoncallback":1,"per_page":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class VimeoSource(BaseTool):
    name = "vimeo"; category = ToolCategory.SOCIAL
    capabilities = ["videos", "channels", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.vimeo.com/videos",params={"query":f"{query} Raipur","per_page":kw.get("num",10)},headers={"Authorization":f"Bearer {self._get_api_key('VIMEO_ACCESS_TOKEN')}"})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MastodonSource(BaseTool):
    name = "mastodon"; category = ToolCategory.SOCIAL
    capabilities = ["toots", "instances", "search", "federated"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            instance=kw.get("instance","mastodon.social")
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://{instance}/api/v2/search",params={"q":f"{query} Raipur","type":"statuses"})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class BlueskySource(BaseTool):
    name = "bluesky"; category = ToolCategory.SOCIAL
    capabilities = ["posts", "search", "feeds", "profiles"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",params={"q":f"{query} Raipur","limit":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class HackerNewsSource(BaseTool):
    name = "hackernews"; category = ToolCategory.SOCIAL
    capabilities = ["stories", "comments", "ask", "show"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://hn.algolia.com/api/v1/search",params={"query":f"{query} Raipur","tags":"story"})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ProductHuntSource(BaseTool):
    name = "producthunt"; category = ToolCategory.SOCIAL; requires_api_key = True
    capabilities = ["products", "hunters", "topics", "collections"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bearer {self._get_api_key('PRODUCTHUNT_TOKEN')}"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("https://api.producthunt.com/v2/api/graphql",json={"query":f'{{ posts(query: "{query}") {{ edges {{ node {{ name description url }} }} }} }}'},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

SOCIAL_REGISTRY = {
    "reddit": RedditSource, "x": XSource, "facebook": FacebookSource,
    "instagram": InstagramSource, "threads": ThreadsSource,
    "linkedin": LinkedInSource, "youtube": YouTubeSource,
    "telegram": TelegramSource, "discord": DiscordSource,
    "pinterest": PinterestSource, "quora": QuoraSource,
    "medium": MediumSource, "substack": SubstackSource,
    "tumblr": TumblrSource, "flickr": FlickrSource,
    "vimeo": VimeoSource, "mastodon": MastodonSource,
    "bluesky": BlueskySource, "hackernews": HackerNewsSource,
    "producthunt": ProductHuntSource,
}
