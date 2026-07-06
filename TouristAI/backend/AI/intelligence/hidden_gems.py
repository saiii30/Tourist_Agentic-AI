from database.postgres import get_connection


def get_hidden_gems(question, city):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            destination_name,
            state,
            hidden_gems
        FROM destinations
        WHERE LOWER(destination_name)=LOWER(%s)
           OR LOWER(state)=LOWER(%s)
        LIMIT 10
    """,(city, city))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results