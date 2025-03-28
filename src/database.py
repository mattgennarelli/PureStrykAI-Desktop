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
            curve TEXT,
            apex REAL
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database schema updated successfully.")

def insert_swing_data(club_type, club_speed, ball_speed, spin_rate,
                      club_path, face_angle, attack_angle, carry_distance,
                      curve, smash_factor=None, apex=None):
    if not smash_factor and club_speed > 0:
        smash_factor = round(ball_speed / club_speed, 2)

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO swings (
                club_type, club_speed, ball_speed, spin_rate,
                club_path, face_angle, attack_angle, smash_factor,
                carry_distance, curve, apex
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            club_type, club_speed, ball_speed, spin_rate,
            club_path, face_angle, attack_angle, smash_factor,
            carry_distance, curve, apex
        ))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Failed to insert swing data into DB:", e)

def fetch_metric_trend_data(metric_name, club_type):
    """Fetches the last 10 values for a specific metric and club, ordered by swing number (not timestamp)."""
    conn = connect_db()
    cursor = conn.cursor()

    query = f"""
        SELECT {metric_name}
        FROM swings
        WHERE club_type = %s AND {metric_name} IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 10
    """
    cursor.execute(query, (club_type,))
    values = [row[0] for row in cursor.fetchall()][::-1]  # reverse to show oldest first

    cursor.close()
    conn.close()

    swing_numbers = list(range(1, len(values) + 1))
    return swing_numbers, values


def get_swing_trends():
    """Retrieve trend analysis for swing metrics, handling None values."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            COUNT(*) AS total_swings,
            COALESCE(AVG(club_path), 0),
            COALESCE(AVG(face_angle), 0),
            COALESCE(AVG(spin_rate), 0),
            COALESCE(AVG(club_speed), 0),
            COALESCE(AVG(carry_distance), 0),
            COALESCE(AVG(ball_speed), 0),
            COALESCE(AVG(apex), 0),
            COALESCE(AVG(attack_angle), 0)
        FROM swings;
    ''')

    trends = cursor.fetchone()
    cursor.close()
    conn.close()

    return {
        "Total Swings": trends[0],
        "Avg Club Path": round(trends[1], 2),
        "Avg Face Angle": round(trends[2], 2),
        "Avg Spin Rate": round(trends[3], 2),
        "Avg Club Speed": round(trends[4], 2),
        "Avg Carry Distance": round(trends[5], 2),
        "Avg Ball Speed": round(trends[6], 2),
        "Avg Apex (Height)": round(trends[7], 2),
        "Avg Attack Angle": round(trends[8], 2)
    }

if __name__ == "__main__":
    initialize_db()
    print("📊 Updated Swing Trends:", get_swing_trends())
