# backend/AI/rag/seed_rag_knowledge.py
import os
import sys

# Ensure parent path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from rag.vectore_store import get_embeddings, DB_PATH

OFFICIAL_TOURISM_DOCUMENTS = [
    Document(
        page_content=(
            "Meenakshi Amman Temple (Madurai) Official Dress Code & Entry Guidelines:\n"
            "DRESS CODE: Strict traditional attire is mandatory for all devotees per Madras High Court and Temple Board directives.\n"
            "- Men: Must wear Dhoti (Vesti) with shirt, Pyjama with Kurta, or formal trousers with a shirt. Shorts, lungis, bermudas, jeans, and sleeveless shirts are strictly prohibited.\n"
            "- Women: Must wear Saree, Half-Saree (Pavadai), or Salwar Kameez / Churidar with a proper Dupatta (upper shawl). Shorts, short skirts, capris, sleeveless tops, jeans, and leggings are strictly prohibited.\n"
            "- Footwear: Shoes, sandals, and socks are strictly forbidden inside the temple complex. Free shoe counter lockers are available at all 4 Gopuram entrance towers."
        ),
        metadata={
            "chunk_id": "tn_mdu_meenakshi_dresscode",
            "destination": "Meenakshi Amman Temple",
            "city": "Madurai",
            "category": "Heritage & Temple Customs",
            "knowledge_type": "temple_information",
            "source_type": "curated_internal",
            "source_domain": "Tamil Nadu Tourism Development Corporation",
            "source_url": "https://tamilnadutourism.tn.gov.in/attractions/meenakshi-amman-temple",
            "trust_score": 100,
            "language": "en"
        }
    ),
    Document(
        page_content=(
            "Meenakshi Amman Temple (Madurai) Photography & Electronics Policy:\n"
            "PHOTOGRAPHY & ELECTRONICS BAN:\n"
            "- Mobile phones, digital cameras, video recorders, smartwatches, tripods, and flash equipment are STRICTLY BANNED inside the temple premises for security and sanctity preservation.\n"
            "- Lockers & Cloakroom: Electronic storage lockers are available at the East and West entrance towers (nominal fee Rs. 10-20).\n"
            "- Commercial filming and flash photography are strictly forbidden across the 14-acre temple complex."
        ),
        metadata={
            "chunk_id": "tn_mdu_meenakshi_photo_policy",
            "destination": "Meenakshi Amman Temple",
            "city": "Madurai",
            "category": "Heritage & Temple Customs",
            "knowledge_type": "local_customs",
            "source_type": "curated_internal",
            "source_domain": "Tamil Nadu Tourism Development Corporation",
            "source_url": "https://tamilnadutourism.tn.gov.in/attractions/meenakshi-amman-temple",
            "trust_score": 100,
            "language": "en"
        }
    ),
    Document(
        page_content=(
            "Meenakshi Amman Temple (Madurai) Timings & Entry Fees:\n"
            "TIMINGS: Open daily from 05:00 AM to 12:30 PM, and 04:00 PM to 10:00 PM.\n"
            "ENTRY FEES: General entry is free for all visitors. Special Darshan Queue tickets cost Rs. 50 / Rs. 100 per person.\n"
            "BEST TIME TO VISIT: Early morning before 09:00 AM or late evening after 07:00 PM to avoid peak pilgrim queues."
        ),
        metadata={
            "chunk_id": "tn_mdu_meenakshi_timings_fees",
            "destination": "Meenakshi Amman Temple",
            "city": "Madurai",
            "category": "Heritage & Culture",
            "knowledge_type": "temple_information",
            "source_type": "curated_internal",
            "source_domain": "Tamil Nadu Tourism Development Corporation",
            "source_url": "https://tamilnadutourism.tn.gov.in/attractions/meenakshi-amman-temple",
            "trust_score": 100,
            "language": "en"
        }
    ),
    Document(
        page_content=(
            "Tirumalai Nayakkar Palace (Madurai) Official Information:\n"
            "TIMINGS: 09:00 AM to 05:00 PM daily. Light & Sound Show at 06:45 PM (English) and 08:00 PM (Tamil).\n"
            "ENTRY FEES: Adults Rs. 25, Children Rs. 10. Camera Fee Rs. 50. Light & Sound Show Ticket Rs. 50.\n"
            "HIGHLIGHTS: 17th-century palace built by King Tirumalai Nayak featuring grand Italianate-Dravidian giant pillars."
        ),
        metadata={
            "chunk_id": "tn_mdu_nayak_palace",
            "destination": "Tirumalai Nayakkar Palace",
            "city": "Madurai",
            "category": "Heritage & Culture",
            "knowledge_type": "history",
            "source_type": "curated_internal",
            "source_domain": "Archaeological Survey of India / Tamil Nadu Tourism",
            "source_url": "https://tamilnadutourism.tn.gov.in/attractions/thirumalai-nayakar-mahal",
            "trust_score": 100,
            "language": "en"
        }
    ),
    Document(
        page_content=(
            "Gandhi Memorial Museum (Madurai) Official Guidelines:\n"
            "TIMINGS: 10:00 AM to 01:00 PM and 02:00 PM to 05:45 PM. Open daily (Closed on Fridays).\n"
            "ENTRY FEES: Free admission for all visitors.\n"
            "HIGHLIGHTS: Houses the original blood-stained dhoti worn by Mahatma Gandhi during his assassination in 1948."
        ),
        metadata={
            "chunk_id": "tn_mdu_gandhi_museum",
            "destination": "Gandhi Memorial Museum",
            "city": "Madurai",
            "category": "Museums & History",
            "knowledge_type": "history",
            "source_type": "curated_internal",
            "source_domain": "Incredible India / Ministry of Tourism",
            "source_url": "https://www.incredibleindia.org/content/incredible-india-v2/en/destinations/madurai/gandhi-memorial-museum.html",
            "trust_score": 100,
            "language": "en"
        }
    ),
    Document(
        page_content=(
            "Madurai Emergency Helplines & Health Support:\n"
            "EMERGENCY NUMBERS: National Emergency 112, Police 100, Ambulance 108.\n"
            "HOSPITALS: Apollo Speciality Hospital (0452-2531044, K.K. Nagar), Government Rajaji Hospital & ER (0452-2532535, Panagal Road).\n"
            "TOURIST POLICE DESK: Madurai Central Railway Station Counter (0452-2334757)."
        ),
        metadata={
            "chunk_id": "tn_mdu_emergency",
            "destination": "Madurai Emergency Contacts",
            "city": "Madurai",
            "category": "Emergency & Helplines",
            "knowledge_type": "safety_tips",
            "source_type": "curated_internal",
            "source_domain": "Madurai District Administration",
            "source_url": "https://madurai.nic.in",
            "trust_score": 100,
            "language": "en"
        }
    )
]

def seed_database():
    print("[INFO] Initializing FAISS Vector Store Seeding...")
    embedding_model = get_embeddings()
    if embedding_model is None:
        print("[ERROR] Embedding model unavailable.")
        return

    try:
        from langchain_community.vectorstores import FAISS

        # Build fresh FAISS database with official documents
        db = FAISS.from_documents(OFFICIAL_TOURISM_DOCUMENTS, embedding_model)
        
        # Save to DB_PATH
        os.makedirs(DB_PATH, exist_ok=True)
        db.save_local(DB_PATH)
        print(f"[SUCCESS] Successfully seeded FAISS vector store at {DB_PATH} with {len(OFFICIAL_TOURISM_DOCUMENTS)} official documents!")
    except Exception as e:
        print(f"[ERROR] Failed to seed FAISS vector store: {e}")

if __name__ == "__main__":
    seed_database()
