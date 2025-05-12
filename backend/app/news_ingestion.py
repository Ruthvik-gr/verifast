import feedparser
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsIngestionService:
    """Service for ingesting news articles from RSS feeds"""
    
    def __init__(self, rss_url: str = "https://www.firstpost.com/commonfeeds/v1/mfp/rss/india.xml"):
        self.rss_url = rss_url
        
    async def fetch_rss_feed(self) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feed"""
        try:
            logger.info(f"Fetching RSS feed from {self.rss_url}")
            feed = feedparser.parse(self.rss_url)
            
            articles = []
            for entry in feed.entries:
                article = {
                    "title": entry.title,
                    "url": entry.link,
                    "published_date": entry.published if hasattr(entry, 'published') else None,
                    "summary": entry.summary if hasattr(entry, 'summary') else None,
                    "content": None
                }
                articles.append(article)
                
            logger.info(f"Fetched {len(articles)} articles from RSS feed")
            return articles
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []
            
    async def fetch_article_content(self, url: str) -> str:
        """Fetch and parse full article content from URL"""
        try:
            logger.info(f"Fetching article content from {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}, status: {response.status}")
                        return ""
                        
                    html = await response.text()
                    
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract main article content (adjust selectors for FirstPost)
            article_content = ""
            
            # Try different selectors commonly used for main content
            selectors = [
                '.article-full-content', 
                'article',
                '.story-content',
                '#content-body',
                '.entry-content',
                '.post-content'
            ]
            
            for selector in selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # Extract paragraphs
                    paragraphs = content_div.find_all('p')
                    article_content = ' '.join([p.get_text().strip() for p in paragraphs])
                    break
            
            # If no content found using selectors, get all paragraphs
            if not article_content:
                logger.warning(f"No specific content found for {url}, extracting all paragraphs")
                paragraphs = soup.find_all('p')
                article_content = ' '.join([p.get_text().strip() for p in paragraphs])
            
            logger.info(f"Fetched {len(article_content)} characters from {url}")
            return article_content
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return "Content unavailable"
            
    async def fetch_articles_with_content(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch articles and their full content"""
        articles = await self.fetch_rss_feed()
        articles = articles[:limit]  # Limit the number of articles
        
        logger.info(f"Fetching content for {len(articles)} articles")
        
        # Create tasks for fetching article content
        tasks = []
        for article in articles:
            task = asyncio.create_task(self.fetch_article_content(article["url"]))
            tasks.append((article, task))
        
        # Process results as they complete
        for article, task in tasks:
            try:
                content = await task
                article["content"] = content
            except Exception as e:
                logger.error(f"Error processing article {article['url']}: {e}")
                article["content"] = "Content unavailable"
                
        # Filter out articles with no content
        articles = [a for a in articles if a["content"] and len(a["content"]) > 100]
        
        logger.info(f"Successfully fetched content for {len(articles)} articles")
        return articles
        
    def save_articles_to_file(self, articles: List[Dict[str, Any]], filename: str = None):
        """Save fetched articles to a JSON file"""
        if filename is None:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"articles_{date_str}.json"
            
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", filename)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(articles)} articles to {filepath}")
        return filepath
        
    async def load_articles_from_file(self, filename: str) -> List[Dict[str, Any]]:
        """Load articles from a JSON file"""
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", filename)
        
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return []
            
        with open(filepath, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            
        logger.info(f"Loaded {len(articles)} articles from {filepath}")
        return articles
        
    async def ingest_articles(self, limit: int = 50, save_to_file: bool = True) -> List[Dict[str, Any]]:
        """Main method to ingest articles"""
        articles = await self.fetch_articles_with_content(limit)
        
        if save_to_file and articles:
            self.save_articles_to_file(articles)
            
        return articles


async def main():
    """Test function to run the ingestion service"""
    service = NewsIngestionService()
    articles = await service.ingest_articles(limit=5)
    print(f"Ingested {len(articles)} articles")
    
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Content length: {len(article['content'])} chars")
        print("---")
        
if __name__ == "__main__":
    asyncio.run(main())
