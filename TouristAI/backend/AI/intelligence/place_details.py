import os, json, sqlite3, requests, urllib.parse
from database.postgres import get_connection
from rag_service import client  # your LLM client, last resort only

UA = {"User-Agent": "TouristAI/1.0"}
WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_API  = "https://en.wikipedia.org/w/api.php"
GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def normalize_name(name: str):
    mapping = {
        "Itmad-ud-Daulah (Baby Taj)": "Tomb of I'timād-ud-Daulah",
        "Baby Taj": "Tomb of I'timād-ud-Daulah",
        "Ellora": "Ellora Caves",
        "Ajanta": "Ajanta Caves",
        "Qutub Minar": "Qutb Minar",
        "Mysore Palace": "Mysore Palace",
    }

    return mapping.get(name.strip(), name.strip())

def _cache_get(name, city):
    conn = sqlite3.connect("place_cache.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS place_cache(
        key TEXT PRIMARY KEY, payload TEXT, ts INTEGER DEFAULT (strftime('%s','now')))""")
    row = conn.execute("SELECT payload FROM place_cache WHERE key=?",
                       (f"{name}|{city}".lower(),)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def _cache_put(name, city, payload):
    conn = sqlite3.connect("place_cache.db")
    conn.execute("INSERT OR REPLACE INTO place_cache(key,payload) VALUES(?,?)",
                 (f"{name}|{city}".lower(), json.dumps(payload)))
    conn.commit(); conn.close()

# ---------- Tier 1: DB ----------
def _from_db(name, city):
    conn = get_connection(); cur = conn.cursor()
    try:
        # cur.execute("""
        #     SELECT a.attraction_name, a.description, a.latitude, a.longitude, a.category
        #     FROM attraction_details a
        #     JOIN destinations d ON a.destination_id = d.id
        #     WHERE LOWER(a.attraction_name)=LOWER(%s)
        #       AND (LOWER(d.destination_name)=LOWER(%s) OR LOWER(d.state)=LOWER(%s))
        #     LIMIT 1
        # """, (name, city, city))
        cur.execute("""
SELECT
    a.attraction_name,
    a.description,
    a.latitude,
    a.longitude,
    a.category
FROM attraction_details a
JOIN destinations d
ON a.destination_id=d.id
WHERE LOWER(a.attraction_name) LIKE LOWER(%s)
AND (
LOWER(d.destination_name)=LOWER(%s)
OR LOWER(d.state)=LOWER(%s)
)
LIMIT 1
""",
("%"+name+"%", city, city))
        r = cur.fetchone()
        if not r: return None
        name_, desc, lat, lon, cat = r
        # only accept if description looks substantive
        # if desc and len(desc) > 120 and lat and lon:
        if (
    desc
    and len(desc) > 120
    and lat is not None
    and lon is not None
):
            return {"name": name_, "history": desc, "lat": float(lat),
                    "lon": float(lon), "category": cat, "source": "db"}
        # partial hit: keep coords, still fetch history elsewhere
        return {"name": name_, "history": desc, "lat": lat and float(lat),
                "lon": lon and float(lon), "category": cat, "source": "db-partial"}
    finally:
        cur.close(); conn.close()

# ---------- Tier 2: Wikipedia ----------
def _from_wikipedia(name, city):
    try:
        s = requests.get(WIKI_API, headers=UA, timeout=6, params={
            "action":"query","list":"search","format":"json",
            "srsearch": f"{name} {city}", "srlimit": 3})
        hits = s.json().get("query",{}).get("search",[])
        for h in hits:
            r = requests.get(WIKI_REST + urllib.parse.quote(h["title"]),
                             headers=UA, timeout=6)
            if r.status_code != 200: continue
            d = r.json()
            if d.get("type") == "disambiguation": continue
            extract = d.get("extract","")
            if len(extract) < 80: continue
            coords = d.get("coordinates") or {}
            return {
                "name": d.get("title", name),
                "history": extract,
                "lat": coords.get("lat"), "lon": coords.get("lon"),
                "image": (d.get("originalimage") or d.get("thumbnail") or {}).get("source"),
                # "wiki_url": (d.get("content_urls") or {}).get("desktop",{}).get("page"),
                "wikiUrl": (d.get("content_urls") or {}).get("desktop",{}).get("page"),
                "source": "wikipedia",
            }
    except Exception: pass
    return None

# ---------- Tier 3: Google Places ----------
def _from_google(name, city):
    if not GOOGLE_KEY: return None
    try:
        find = requests.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={"input": f"{name} {city}", "inputtype":"textquery",
                    "fields":"place_id,geometry", "key": GOOGLE_KEY}, timeout=6).json()
        cand = (find.get("candidates") or [None])[0]
        if not cand: return None
        pid = cand["place_id"]
        loc = cand["geometry"]["location"]
        det = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": pid, "key": GOOGLE_KEY,
                    "fields":"name,editorial_summary,formatted_address"}, timeout=6).json()
        res = det.get("result",{})
        return {
            "name": res.get("name", name),
            "history": (res.get("editorial_summary") or {}).get("overview") or "",
            "lat": loc["lat"], "lon": loc["lng"],
            "address": res.get("formatted_address"),
            "source": "google_places",
        }
    except Exception: return None

# ---------- Tier 4: OSM (geocode only) ----------
def _from_osm(name, city):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
            headers=UA, timeout=6,
            params={"q": f"{name}, {city}", "format":"json", "limit":1}).json()
        if not r: return None
        return {"name": name, "history": "", "lat": float(r[0]["lat"]),
                "lon": float(r[0]["lon"]), "source": "osm"}
    except Exception: return None

# ---------- Tier 5: LLM last resort ----------
def _from_llm(name, city):
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":
                f"Give a 4-sentence factual history of the tourist place '{name}' in {city}. "
                f"If you are not sure it exists, reply exactly: UNKNOWN."}],
            temperature=0.2)
        text = resp.choices[0].message.content.strip()
        if "UNKNOWN" in text.upper(): return None
        return {"name": name, "history": text, "lat": None, "lon": None,
                "source": "llm", "warning": "AI-generated; verify."}
    except Exception: return None

# ---------- Orchestrator ----------
def get_place_details(name: str, city: str) -> dict:
    name = normalize_name(name)
    cached = _cache_get(name, city)
    if cached: return cached

    result = _from_db(name, city) or {}
    # If DB gave partial info, keep filling missing pieces
    for fetcher in (_from_wikipedia, _from_google, _from_osm):
        if result.get("history") and result.get("lat") and result.get("lon"):
            break
        extra = fetcher(name, city)
        if not extra: continue
        for k, v in extra.items():
            if v and not result.get(k):
                result[k] = v

    if not result.get("history"):
        llm = _from_llm(name, city)
        if llm:
            for k,v in llm.items():
                result.setdefault(k, v)

    if not result:
        result = {"name": name, "history": "No information available.",
                  "lat": None, "lon": None, "source": "none"}

    _cache_put(name, city, result)
    return result
