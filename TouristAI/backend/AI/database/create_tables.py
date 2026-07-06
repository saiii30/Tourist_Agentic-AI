from postgres import get_connection

conn = get_connection()

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS attractions(
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    country VARCHAR(100),
    attraction_name VARCHAR(255),
    category VARCHAR(100),
    rating DECIMAL(2,1),
    popularity INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS query_cache(
    id SERIAL PRIMARY KEY,
    question TEXT UNIQUE,
    answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute(""" CREATE TABLE IF NOT EXISTS attraction_details(

    id SERIAL PRIMARY KEY,

    destination_id INTEGER REFERENCES destinations(id),

    attraction_name VARCHAR(255),

    category VARCHAR(100),

    description TEXT,

    popularity_level VARCHAR(20),

    risk_level VARCHAR(20),

    family_friendly BOOLEAN,

    best_visit_time VARCHAR(50),

    visit_duration VARCHAR(50),

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION
);""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS destinations(
    id SERIAL PRIMARY KEY,
    destination_name VARCHAR(255),
    state VARCHAR(255),
    region VARCHAR(255),
    popularity_score INTEGER,
    safety_rating INTEGER,
    hidden_gems JSONB,
    primary_attractions JSONB,
    activities_available JSONB,
    trip_types JSONB,
    ideal_days INTEGER
);
""")
conn.commit()

cursor.close()
conn.close()

print("Tables Created Successfully")