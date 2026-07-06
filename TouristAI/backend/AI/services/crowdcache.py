import time
import threading
from services.crowd_service import predict_crowd

# key -> (expiry_epoch, payload)
_CACHE = {}
_LOCK = threading.Lock()
TTL = 30 * 60   # 30 minutes

def getcrowd(city, attraction_name, popularity, bestvisittime):
    """
    Returns cached crowd prediction. Recomputes every 30 minutes.
    """
    key = f"{city.lower()}::{attraction_name.lower()}"
    now = time.time()

    with _LOCK:
        entry = _CACHE.get(key)
        if entry and entry[0] > now:
            payload = dict(entry[1])
            payload["cached"] = True
            payload["nextrefresh"] = int(entry[0] - now)
            return payload

    # compute outside the lock (weather call can be slow)
    result = predict_crowd(city, popularity, bestvisittime)

    payload = {
        "attraction": attraction_name,
        "city": city,
        "level": result["crowd"],           # Very High / High / Medium / Low
        "emoji": result["emoji"],
        "score": result["score"],
        "maxscore": 20,                     # for the gauge %
        "reasons": result["reasons"],       # ["Weekend","Sunburn Festival","Clear weather"]
        "advice": result["advice"],
        "weather": result["weather"],
        "updatedat": int(now),
        "nextrefresh": TTL,
        "cached": False,
    }

    with _LOCK:
        _CACHE[key] = (now + TTL, payload)

    return payload




# import time
# import threading

# from services.crowd_service import predict_crowd

# _CACHE = {}
# _LOCK = threading.Lock()
# TTL = 30 * 60   # 30 minutes


# def getcrowd(city, attraction_name, popularity, bestvisittime):
#     key = f"{city.lower()}::{attraction_name.lower()}"
#     now = time.time()

#     with _LOCK:
#         entry = _CACHE.get(key)
#         if entry and entry[0] > now:
#             payload = dict(entry[1])
#             payload["cached"] = True
#             payload["nextrefresh"] = int(entry[0] - now)
#             return payload

#     # NEW: attraction name is passed so history lookup can run
#     result = predict_crowd(city, popularity, bestvisittime, attraction=attraction_name)

#     payload = {
#         "attraction": attraction_name,
#         "city":       city,
#         "level":      result["crowd"],
#         "emoji":      result["emoji"],
#         "score":      result["score"],
#         "maxscore":   20,
#         "reasons":    result["reasons"],
#         "advice":     result["advice"],
#         "weather":    result["weather"],
#         "history":    result.get("history"),
#         "updatedat":  int(now),
#         "nextrefresh": TTL,
#         "cached":     False,
#     }

#     with _LOCK:
#         _CACHE[key] = (now + TTL, payload)

#     return payload

