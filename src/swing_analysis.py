import os
import psycopg2
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from database import fetch_metric_trend_data


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
               attack_angle, smash_factor, distance, launch_angle, apex, curve
        FROM swings
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row:
        keys = ["id", "club_type", "club_speed", "ball_speed", "spin_rate", "club_path", "face_angle",
                "attack_angle", "smash_factor", "distance", "launch_angle", "apex", "curve"]
        swing_data = dict(zip(keys, row))
        swing_data["carry_distance"] = swing_data.pop("distance")
        return swing_data
    else:
        return None


def construct_dynamic_prompt(swing_data):
    club = swing_data.get('club_type', 'club')
    face_angle = swing_data.get("face_angle")
    print("Face angle raw value:", face_angle)

    prompt = f"""You are a professional golf swing coach analyzing a shot taken with a {club}.
    The goal is to identify any potential swing flaws based on the player's numbers, compared to what is typical for a well-struck shot using that club.
    Metrics: """
    for metric, value in swing_data.items():
        if value is not None:
            prompt += f"- {metric.replace('_', ' ').title()}: {value}\n"

    prompt += """
    Instructions:
    - Use your expertise to determine whether each metric is ideal, borderline, or problematic.
    - Face angle sign convention: negative = closed (left), positive = open (right).
    - For irons, attack angle should generally be negative. Positive values indicate incorrect strike mechanics.
    - Curve values under 10 yards (L or R) are minor and may be acceptable depending on face/path alignment.
    - Return a JSON object where each metric has:
        - "issue": what’s wrong, or "N/A"
        - "severity": 0–100 score where 100 = perfect
        - "description": brief explanation
        - "drill": specific drill to improve or "N/A"
    Only analyze metrics provided. Do NOT add new ones. Reply ONLY in JSON.
    """
    return prompt

def construct_trend_prompt(values, metric, club_type):
    return f"""
        You are a golf swing coach reviewing a golfer's last 10 swings using a {club_type}. The metric of focus is {metric.replace('_', ' ')}.
        Values: {values}

        Evaluate the trend over these swings:
        - Is the metric improving, getting worse, or inconsistent?
        - Is the current value near the expected range for a {club_type}?
        - What could be causing issues based on the pattern?
        - What drill do you recommend to improve this metric?

        Respond in clear JSON:
        {{
        "trend_summary": "...",
        "diagnosis": "...",
        "recommendation": "..."
        }}
        """

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
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0
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

def get_available_clubs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT club_type FROM swings
        WHERE club_type IS NOT NULL
        ORDER BY club_type
    """)
    clubs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return clubs


def run_analysis(self):
    print("🔄 Running swing analysis...")

    swing_data = swing_analysis.fetch_latest_swing()
    if not swing_data:
        print("⚠️ No swing data found.")
        self._show_message_table("⚠️ No swing data found.")
        return

    prompt = swing_analysis.construct_dynamic_prompt(swing_data)
    print("📤 Prompt sent to GPT:\n", prompt)

    analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)
    print("📥 Raw GPT response:\n", analysis_json)

    def is_meaningful_analysis(data):
        return isinstance(data, dict) and any(
            isinstance(v, dict) and v.get("issue") != "N/A"
            for v in data.values()
        )

    if not is_meaningful_analysis(analysis_json):
        print("⚠️ First analysis was empty or unhelpful. Retrying once...")
        analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)

    if "error" in analysis_json:
        print("❌ GPT Error:", analysis_json["error"])
        self._show_message_table(f"❌ Error: {analysis_json['error']}")
        return

    swing_analysis.save_analysis(swing_data["id"], analysis_json)
    print("✅ Saved analysis to DB.")
    self.display_feedback_table(swing_data, analysis_json)


if __name__ == "__main__":
    run_analysis()