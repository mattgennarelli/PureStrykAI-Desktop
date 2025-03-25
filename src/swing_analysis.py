import os
import psycopg2
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def connect_db():
    return psycopg2.connect(
        dbname="purestrykai",
        user="matthew",
        password="purestrykadmin",
        host="localhost",
        port="5432"
    )

def fetch_latest_swing():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, club_type, club_speed, ball_speed, spin_rate, club_path, face_angle,
               attack_angle, smash_factor, distance, launch_angle, apex, sidespin, curve
        FROM swings
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row:
        keys = ["id", "club_type", "club_speed", "ball_speed", "spin_rate", "club_path", "face_angle",
                "attack_angle", "smash_factor", "distance", "launch_angle", "apex", "sidespin", "curve"]
        swing_data = dict(zip(keys, row))
        swing_data["carry_distance"] = swing_data.pop("distance")
        swing_data["backspin"] = swing_data["spin_rate"]
        return swing_data
    else:
        return None

def construct_dynamic_prompt(swing_data):
    prompt = f"Analyze this golf swing shot using a {swing_data.get('club_type', 'club')}:\n\n"
    prompt += "Metrics:\n"
    for metric, value in swing_data.items():
        if value is not None:
            prompt += f"- {metric.replace('_', ' ').title()}: {value}\n"
    prompt += """
        For each provided metric, respond strictly in JSON with:
        - "issue": Briefly describe any issue or "N/A".
        - "severity": Numeric severity rating (100=perfect, 0=critical).
        - "description": Explain the rating briefly.
        - "drill": Recommended drill or "N/A".
        Only analyze provided metrics. Respond strictly in JSON.
    """
    return prompt

def parse_gpt_response(content):
    content = re.sub(r'^```json|```$', '', content.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        else:
            return {"error": "GPT returned non-dict JSON.", "raw_response": content}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON from GPT", "raw_response": content}

def analyze_swing_with_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return parse_gpt_response(content)
    except Exception as e:
        return {"error": str(e)}

def save_analysis(swing_id, analysis_json):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO swing_analysis (swing_id, analysis_json)
        VALUES (%s, %s)
    """, (swing_id, json.dumps(analysis_json)))
    conn.commit()
    cursor.close()
    conn.close()

def get_available_metrics():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'swings'
    """)
    all_metrics = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    ignore_columns = {"id", "timestamp", "club_type"}
    return [metric for metric in all_metrics if metric not in ignore_columns]

def run_analysis():
    swing_data = fetch_latest_swing()
    if not swing_data:
        print("⚠️ No swing data found.")
        return
    prompt = construct_dynamic_prompt(swing_data)
    analysis = analyze_swing_with_gpt(prompt)
    save_analysis(swing_data['id'], analysis)
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    run_analysis()