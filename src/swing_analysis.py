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
        user="matthew",  # Update with your username
        password="purestrykadmin",  # Update with your password
        host="localhost",
        port="5432"
    )

def fetch_latest_swing():
    conn = psycopg2.connect(
        dbname="purestrykai",
        user="matthew",
        password="purestrykadmin",
        host="localhost",
        port="5432"
    )
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

        # explicitly map column names clearly
        swing_data["carry_distance"] = swing_data.pop("distance")
        swing_data["backspin"] = swing_data["spin_rate"]  # explicitly map clearly

        return swing_data
    else:
        print("⚠️ No swing data found.")
        return None


def construct_prompt(swing_data):
    prompt = f"""
    Analyze the following golf swing shot data using a {swing_data['club_type']}:

    {json.dumps(swing_data, indent=4)}

    Provide structured feedback strictly in these categories ONLY IN VALID JSON FORMAT (use "N/A" if no issue):
    1. Spin Rate Issue (High, Low, N/A): Description & Drill.
    2. Club Path Issue (Too Inside-Out, Too Outside-In, N/A): Description & Drill.
    3. Face Angle Issue (Closed, Open, N/A): Description & Drill.
    4. Attack Angle Issue (Too Steep, Too Shallow, N/A): Description & Drill.
    5. Smash Factor Issue (Poor Contact, N/A): Description & Drill.
    6. Launch Angle Issue (Too High, Too Low, N/A): Description & Drill.
    7. Apex Issue (Too High, Too Low, N/A): Description & Drill.
    8. Sidespin Issue (Hook Spin, Slice Spin, N/A): Description & Drill.

    Your entire response must be valid JSON format with keys as categories and contain absolutely no other text.
    """
    return prompt

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

def analyze_swing_with_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    # Explicitly remove markdown ```json``` formatting if present
    content = re.sub(r'^```json|```$', '', content, flags=re.MULTILINE).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print("⚠️ GPT did not return valid JSON.")
        return {"error": "Invalid JSON from GPT", "raw_response": content}


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

def run_analysis():
    swing_data = fetch_latest_swing()
    prompt = construct_dynamic_prompt(swing_data)
    analysis = analyze_swing_with_gpt(prompt)
    save_analysis(swing_data['id'], analysis)
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    run_analysis()
