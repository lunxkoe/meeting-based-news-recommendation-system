from typing import List, Dict, Optional
from newspaper import Article
import asyncio
from domain.interfaces.crawler import ICrawlerClient

class NewspaperCrawlerAdapter(ICrawlerClient):
    def _crawl_one(self, url: str) -> Dict[str, Optional[str]]:
        try:
            article = Article(url)
            article.download()
            article.parse()
            return {
                "url": url,
                "title": article.title,
                "original": article.text,
                "summary": None
            } if article.title and article.text else None
        except:
            return None

    async def crawl_urls(self, urls: List[str]) -> List[Dict[str, Optional[str]]]:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(None, self._crawl_one, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [res for res in results if res is not None]