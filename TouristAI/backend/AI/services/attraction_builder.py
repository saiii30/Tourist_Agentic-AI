# from services.crowd_service import predict_crowd


# class AttractionBuilder:

#     @staticmethod
#     def build(city: str, discover_result: dict):

#         attractions = []

#         all_places = (
#             discover_result.get("popular", [])
#             + discover_result.get("medium", [])
#             + discover_result.get("hidden", [])
#         )

#         for idx, place in enumerate(all_places, start=1):

#             crowd = predict_crowd(
#                 city,
#                 place.get("popularity", ""),
#                 place.get("best_time", "")
#             )

#             attractions.append({
#                 "id": str(idx),
#                 "name": place.get("name", ""),
#                 "image": "",
#                 "category": place.get("category", ""),
#                 "distance": place.get("duration", ""),
#                 "expectedCrowd": crowd.get("crowd", "Unknown"),
#                 "bestTime": place.get("best_time", "")
#             })

#         return attractions





from services.crowd_service import predict_crowd


class AttractionBuilder:

    @staticmethod
    def build(city: str, discover_result: dict):
        attractions = []

        all_places = (
            discover_result.get("popular", [])
            + discover_result.get("medium", [])
            + discover_result.get("hidden", [])
        )

        for idx, place in enumerate(all_places, start=1):
            name = place.get("name", "")

            # SAME call signature the discover/chat path uses,
            # so crowd numbers match what AIChat shows.
            # crowd = predict_crowd(
            #     city=city,
            #     attraction=name,                       # <-- pass exact name, not popularity
            # )
            crowd = predict_crowd(
    city=city,
    popularity=place.get("popularity", "Medium"),
    best_visit_time=place.get("best_time", "Morning"),
    attraction=name,
)

            # attractions.append({
            #     "id": str(idx),
            #     "name": name,
            #     # pass through the enriched fields the discover agent already resolved
            #     "image":     place.get("image")     or place.get("thumbnail") or "",
            #     "wikiUrl":   place.get("wiki_url")  or place.get("wikiUrl")   or "",
            #     "lat":       place.get("lat"),
            #     "lon":       place.get("lon"),
            #     "category":  place.get("category", ""),
            #     "distance":  place.get("duration", ""),
            #     "expectedCrowd": crowd.get("crowd", "Unknown"),
            #     "bestTime":  place.get("best_time", ""),
            # })
            #changing the append block with below from codex
            attractions.append({
               "id": str(idx),
               "name": name,
               "image": place.get("image") or "",
               "wikiUrl": place.get("wiki_url") or "",
               "lat": place.get("lat") if place.get("lat") is not None else place.get("latitude"),
               "lon": place.get("lon") if place.get("lon") is not None else place.get("longitude"),
               "category": place.get("category", ""),
               "distance": place.get("duration", ""),
               "popularity": place.get("popularity", "Medium"),
               "expectedCrowd": crowd.get("crowd", "Unknown"),
               "bestTime": place.get("best_time", "Morning"),
})

        return attractions
