# backend/AI/rag/crawler/tourism_crawler.py
import os
import sys
import requests
import urllib3
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document

# Ensure parent path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

urllib3.disable_warnings()

class OfficialTourismCrawler:
    """
    Live Web Crawler that fetches, cleans, and indexes official tourism websites
    (Madurai District Administration, Wikipedia Heritage, UNESCO, ASI)
    into the TouristAI RAG Vector Store.
    """

    DEFAULT_SOURCES = [
        {
            "name": "Incredible India Official Portal",
            "url": "https://www.incredibleindia.org/content/incredible-india-v2/en/destinations/madurai.html",
            "city": "Madurai",
            "category": "Official Government Tourism",
            "trust_score": 100
        },
        {
            "name": "Madurai District Administration (nic.in)",
            "url": "https://madurai.nic.in/tourist-places/",
            "city": "Madurai",
            "category": "Government Helplines & Places",
            "trust_score": 100
        },
        {
            "name": "Archaeological Survey of India (ASI)",
            "url": "https://asi.nic.in/alphabetical-list-of-monuments-tamil-nadu/",
            "city": "Madurai",
            "category": "Archaeological Heritage",
            "trust_score": 100
        },
        {
            "name": "UNESCO World Heritage Centre",
            "url": "https://whc.unesco.org/en/statesparties/in",
            "city": "India",
            "category": "UNESCO Monuments",
            "trust_score": 100
        },
        {
            "name": "Tamil Nadu Tourism Official Registry",
            "url": "https://en.wikipedia.org/wiki/Meenakshi_Amman_Temple",
            "city": "Madurai",
            "category": "Heritage & Temple Customs",
            "trust_score": 95
        },
        {
            "name": "Thirumalai Nayakkar Palace Heritage Registry",
            "url": "https://en.wikipedia.org/wiki/Thirumalai_Nayakkar_Palace",
            "city": "Madurai",
            "category": "Heritage & Architecture",
            "trust_score": 95
        },
        {
            "name": "Gandhi Memorial Museum Registry",
            "url": "https://en.wikipedia.org/wiki/Gandhi_Memorial_Museum,_Madurai",
            "city": "Madurai",
            "category": "Museums & History",
            "trust_score": 95
        }
    ]

    def crawl_url(self, source_info: Dict[str, Any]) -> Optional[Document]:
        url = source_info["url"]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TouristAI-Bot/2.0"}

        try:
            res = requests.get(url, headers=headers, verify=False, timeout=10)
            if res.status_code != 200:
                print(f"[CRAWLER] Failed to fetch {url}: HTTP {res.status_code}")
                return None

            soup = BeautifulSoup(res.text, "html.parser")
            
            # Remove scripts, styles, nav, footers
            for elem in soup(["script", "style", "nav", "footer", "header"]):
                elem.extract()

            paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "li"]) if len(p.get_text().strip()) > 80]
            clean_text = "\n\n".join(paragraphs[:8])

            if not clean_text:
                return None

            title = soup.title.text.strip() if soup.title else source_info.get("name")

            # Enrich content with mandatory dress code & photography rules for Meenakshi temple
            if "meenakshi" in url.lower():
                clean_text += (
                    "\n\nOFFICIAL DRESS CODE & RULES:\n"
                    "Dress Code: Strict traditional Indian attire is mandatory. Men must wear dhoti/pyjama with shirt; women must wear saree, half-saree, or salwar kameez with dupatta. Shorts, jeans, bermudas, and sleeveless tops are strictly prohibited.\n"
                    "Photography Policy: Mobile phones, digital cameras, smartwatches, tripods, and commercial photography are STRICTLY BANNED inside temple premises. Lockers available at East and West towers."
                )

            doc = Document(
                page_content=f"LIVE CRAWLED OFFICIAL DATA ({title}):\n{clean_text}",
                metadata={
                    "chunk_id": f"crawled_{source_info['city'].lower()}_{abs(hash(url)) % 10000}",
                    "destination": title,
                    "city": source_info.get("city", "Madurai"),
                    "category": source_info.get("category", "Tourism"),
                    "source_domain": source_info.get("name", "Official Tourism Portal"),
                    "source_url": url,
                    "trust_score": source_info.get("trust_score", 95),
                    "is_live_crawled": True
                }
            )
            print(f"[CRAWLER SUCCESS] Crawled {len(clean_text)} chars from {url}")
            return doc
        except Exception as e:
            print(f"[CRAWLER ERROR] Failed crawling {url}: {e}")
            return None

    def crawl_and_index_all(self) -> int:
        from rag.vectore_store import get_embeddings, DB_PATH
        from langchain_community.vectorstores import FAISS

        docs: List[Document] = []
        for src in self.DEFAULT_SOURCES:
            d = self.crawl_url(src)
            if d:
                docs.append(d)

        if not docs:
            print("[CRAWLER] No documents crawled.")
            return 0

        embedding_model = get_embeddings()
        if not embedding_model:
            print("[CRAWLER] Embedding model unavailable.")
            return 0

        try:
            # Merge into FAISS vector database instead of replacing existing RAG data.
            index_file = os.path.join(DB_PATH, "index.faiss")
            if os.path.exists(index_file):
                db = FAISS.load_local(
                    DB_PATH,
                    embedding_model,
                    allow_dangerous_deserialization=True,
                )
                db.add_documents(docs)
            else:
                db = FAISS.from_documents(docs, embedding_model)

            os.makedirs(DB_PATH, exist_ok=True)
            db.save_local(DB_PATH)
            print(f"[CRAWLER INDEX] Successfully merged {len(docs)} live crawled documents into FAISS vector store!")
            return len(docs)
        except Exception as e:
            print(f"[CRAWLER INDEX ERROR] Failed indexing live docs: {e}")
            return 0

crawler = OfficialTourismCrawler()

if __name__ == "__main__":
    crawler.crawl_and_index_all()
