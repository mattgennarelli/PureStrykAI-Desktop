import psycopg2

def connect_db():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname="purestrykai",
        user="matthew",  # Change to your PostgreSQL username
        password="your_secure_password",  # Change to your PostgreSQL password
        host="localhost",
        port="5432"
    )

def initialize_db():
    """Create the swings table with updated fields."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS swings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    club_type TEXT,
    club_path REAL,
    face_angle REAL,
    attack_angle REAL,
    spin_rate REAL,
    club_speed REAL,
    ball_speed REAL,
    smash_factor REAL,
    carry_distance REAL,
    launch_angle REAL,
    apex REAL,
    sidespin REAL,
    curve TEXT
)
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database schema updated successfully.")

def insert_swing_data(club_type, club_speed, ball_speed, spin_rate, club_path, face_angle, attack_angle, carry_distance, curve, smash_factor=None):
    if not smash_factor:
        smash_factor = round(ball_speed / club_speed, 2)

    conn = sqlite3.connect('data/swing_data.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO swings (club_type, club_speed, ball_speed, spin_rate, club_path, face_angle, attack_angle, smash_factor, carry_distance, curve)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (club_type, club_speed, ball_speed, spin_rate, club_path, face_angle, attack_angle, smash_factor, carry_distance, curve))

    conn.commit()
    conn.close()

def fetch_metric_trend_data(metric_name):
    """Fetches trend data for a specific metric from the PostgreSQL database."""
    conn = connect_db()
    cursor = conn.cursor()

    query = f"""
        SELECT timestamp, {metric_name}
        FROM swings
        WHERE {metric_name} IS NOT NULL
        ORDER BY timestamp ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    # Separate the list of tuples into two lists
    timestamps = [row[0] for row in results]
    values = [row[1] for row in results]

    return timestamps, values


def get_swing_trends():
    """Retrieve trend analysis for swing metrics, handling None values."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            COUNT(*) AS total_swings,
            COALESCE(AVG(club_path), 0) AS avg_club_path,
            COALESCE(AVG(face_angle), 0) AS avg_face_angle,
            COALESCE(AVG(backspin), 0) AS avg_backspin,
            COALESCE(AVG(club_speed), 0) AS avg_club_speed,
            COALESCE(AVG(distance), 0) AS avg_distance,
            COALESCE(AVG(ball_speed), 0) AS avg_ball_speed,
            COALESCE(AVG(apex), 0) AS avg_apex,
            COALESCE(AVG(launch_angle), 0) AS avg_launch_angle,
            COALESCE(AVG(sidespin), 0) AS avg_sidespin
        FROM swings;
    ''')

    trends = cursor.fetchone()
    conn.close()

    return {
        "Total Swings": trends[0],
        "Avg Club Path": round(trends[1], 2),
        "Avg Face Angle": round(trends[2], 2),
        "Avg Backspin": round(trends[3], 2),
        "Avg Club Speed": round(trends[4], 2),
        "Avg Distance": round(trends[5], 2),
        "Avg Ball Speed": round(trends[6], 2),
        "Avg Apex": round(trends[7], 2),
        "Avg Launch Angle": round(trends[8], 2),
        "Avg Sidespin": round(trends[9], 2),
    }

if __name__ == "__main__":
    initialize_db()
    print("📊 Updated Swing Trends:", get_swing_trends())
