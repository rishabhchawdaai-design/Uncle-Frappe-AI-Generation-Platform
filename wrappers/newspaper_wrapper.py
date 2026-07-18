"""17. newspaper3k - News article extraction."""
import time
from .base import BaseCollector, CollectorResult

class NewspaperCollector(BaseCollector):
    name = "newspaper3k"
    capabilities = ["news_extraction", "article_parsing", "metadata", "NLP", "multi_language"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from newspaper import Article
            article = Article(url, language=kwargs.get("language", "en"))
            article.download()
            article.parse()
            try:
                article.nlp()
            except Exception:
                pass
            return CollectorResult(
                url=url, content=article.text,
                title=article.title,
                metadata={
                    "authors": article.authors,
                    "publish_date": str(article.publish_date),
                    "summary": article.summary,
                    "keywords": article.keywords,
                    "top_image": article.top_image,
                },
                collector=self.name, duration_ms=self._timing(start),
            )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
