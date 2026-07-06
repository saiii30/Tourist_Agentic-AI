# from flask import Blueprint, request, jsonify
# from database.postgres import get_connection
# from services.crowdcache import getcrowd

# crowdbp = Blueprint("crowd", __name__)

# @crowdbp.route("/api/crowd", methods=["GET"])
# def crowdendpoint():
#     city = request.args.get("city")
#     attraction = request.args.get("attraction")

#     if not city or not attraction:
#         return jsonify({"error": "city and attraction required"}), 400

#     # look up popularity + besttime from DB (cheap; single row)
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute("""
#             SELECT a.popularity_level, a.best_visit_time
#             FROM attraction_details a
#             JOIN destinations d ON d.id = a.destination_id
#             WHERE LOWER(d.destination_name) = LOWER(%s)
#               AND LOWER(a.attraction_name) = LOWER(%s)
#             LIMIT 1
#         """, (city, attraction))
#         row = cursor.fetchone()
#     finally:
#         cursor.close()
#         conn.close()

#     if not row:
#         return jsonify({"error": "attraction not found"}), 404

#     popularity, besttime = row[0] or "Medium", row[1] or "Morning"
#     payload = getcrowd(city, attraction, popularity, besttime)
#     return jsonify(payload)



