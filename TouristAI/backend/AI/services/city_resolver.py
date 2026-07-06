from database.postgres import get_connection


SIMILARITY_THRESHOLD = 0.45


def resolve_city(user_city: str):
    """
    Resolves user entered city/state with spelling mistakes.

    Example:
    Chickmagalore -> Chikkamagaluru
    Banglore -> Bengaluru
    Madras -> Chennai (if present in DB)

    Returns:
        Canonical destination name
    """

    if not user_city:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                destination_name,
                state,
                GREATEST(
                    similarity(lower(destination_name), lower(%s)),
                    similarity(lower(state), lower(%s))
                ) AS score

            FROM destinations

            ORDER BY score DESC

            LIMIT 1;
            """,
            (user_city, user_city),
        )

        result = cursor.fetchone()

        if result:

            destination_name = result[0]
            state = result[1]
            score = result[2]

            if score >= SIMILARITY_THRESHOLD:

                print(
                    f"[City Resolver] '{user_city}' -> '{destination_name}' (score={score:.2f})"
                )

                return destination_name

        print(f"[City Resolver] No close match found for '{user_city}'")

        return user_city

    finally:

        cursor.close()
        conn.close()