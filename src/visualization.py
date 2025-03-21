import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import swing_analysis
import datetime



def plot_latest_swing_radar():
    latest_swing = swing_analysis.fetch_latest_swing()
    prompt = swing_analysis.construct_dynamic_prompt(latest_swing)
    analysis = swing_analysis.analyze_swing_with_gpt(prompt)

    metrics = analysis.get("metrics", {})

    # **Ensure all metrics are included, even if "N/A"**
    all_metrics = [
        "Club Speed", "Ball Speed", "Spin Rate", "Club Path",
        "Face Angle", "Attack Angle", "Launch Angle", "Curve", "Backspin"
    ]

    labels = []
    severities = []

    for metric in all_metrics:
        details = metrics.get(metric, {})  # Get metric details safely
        severity = details.get("severity", 100)
        
        labels.append(metric)
        severities.append(severity)

    # **Ensure Radar Chart is circular**
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    severities += severities[:1]
    angles += angles[:1]

    # **Create radar chart**
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, severities, color='orange', alpha=0.6)
    ax.plot(angles, severities, color='black', linewidth=1.5)

    # **Format Chart**
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    plt.title("Swing Performance - Overall Metrics", size=14, pad=20)

    plt.show()

##########Swing trend
def plot_swing_trend(metric):
    conn = swing_analysis.connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT timestamp, {metric} FROM swings ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()

    if not rows or len(rows) < 2:
        print(f"⚠️ Not enough data to show trend for {metric}")
        return

    shot_numbers = list(range(1, len(rows) + 1))  # **Generate Shot Indexes (1,2,3,4...)**
    values = [row[1] for row in rows if row[1] is not None]  # **Ignore None values**

    plt.figure(figsize=(8, 5))
    plt.plot(shot_numbers, values, marker='o', linestyle='-', color='b', markersize=8, markerfacecolor='red')

    plt.xlabel("Shot Number")
    plt.ylabel(metric.replace("_", " ").title())
    plt.title(f"{metric.replace('_', ' ').title()} Over Shots")

    plt.xticks(shot_numbers)  # Ensure X-axis shows each shot number
    plt.grid()
    plt.show()