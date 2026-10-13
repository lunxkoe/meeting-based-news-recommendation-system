from typing import List
import httpx
import asyncio
from domain.interfaces.search import ISearchClient

class GoogleSearchAdapter(ISearchClient):
    def __init__(self, json_api_key: str, engine_id: str):
        self.api_key = json_api_key
        self.engine_id = engine_id
        self.api_url = "https://www.googleapis.com/customsearch/v1"

    async def search_urls(self, keywords: List[str], count: int = 50) -> List[str]:
        if not self.api_key or not self.engine_id:
            return []
        
        query = " ".join(keywords) + " news -filetype:pdf"
        news_per_request = 10
        num_requests = count // news_per_request
        
        tasks = []
        timeout = httpx.Timeout(30.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            for i in range(num_requests):
                start_index = 1 + i * news_per_request
                params = {
                    "key": self.api_key,
                    "cx": self.engine_id,
                    "q": query,
                    "num": news_per_request,
                    "start": start_index,
                    "sort": "date"
                }
                tasks.append(client.get(self.api_url, params=params))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        urls = set()
        for res in responses:
            if isinstance(res, httpx.Response) and res.status_code == 200:
                try:
                    items = res.json().get('items', [])
                    for item in items:
                        urls.add(item['link'])
                except:
                    pass
                    
        return list(urls)