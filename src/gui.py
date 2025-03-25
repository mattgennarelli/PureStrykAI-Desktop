import sys
import json
import swing_analysis
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QComboBox,
    QHBoxLayout, QTextEdit, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from visualization import RadarChart, TrendChart

class SwingAnalysisGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PureStrykAI Swing Analysis")
        self.setMinimumWidth(1000)

        self.main_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.analyze_button = QPushButton("Analyze Latest Swing")
        self.analyze_button.clicked.connect(self.run_analysis)
        self.scroll_layout.addWidget(self.analyze_button)

        self.feedback_label = QLabel("🤖 <b>AI Feedback & Recommendations</b>")
        self.feedback_label.setStyleSheet("font-size: 16px; margin-top: 10px;")
        self.scroll_layout.addWidget(self.feedback_label)

        self.feedback_display = QLabel("")
        self.feedback_display.setWordWrap(True)
        self.feedback_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.scroll_layout.addWidget(self.feedback_display)

        self.radar_chart = RadarChart()
        self.radar_chart.hide()
        self.scroll_layout.addWidget(self.radar_chart)

        # Metric Selector and Button
        metric_layout = QHBoxLayout()
        self.metric_label = QLabel("Select Metric:")
        metric_layout.addWidget(self.metric_label)

        self.metric_selector = QComboBox()
        metric_layout.addWidget(self.metric_selector)

        self.trend_button = QPushButton("Track Progress")
        self.trend_button.clicked.connect(self.update_trend_chart)
        metric_layout.addWidget(self.trend_button)

        self.scroll_layout.addLayout(metric_layout)

        self.trend_chart = TrendChart()
        self.scroll_layout.addWidget(self.trend_chart)

        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

        self.populate_metric_selector()

    def populate_metric_selector(self):
        metrics = swing_analysis.get_available_metrics()
        self.metric_selector.clear()
        self.metric_selector.addItems(metrics)

    def run_analysis(self):
        swing_data = swing_analysis.fetch_latest_swing()
        if not swing_data:
            self.feedback_display.setText("⚠️ No swing data found.")
            return

        prompt = swing_analysis.construct_dynamic_prompt(swing_data)
        analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)

        def is_meaningful_analysis(data):
            return isinstance(data, dict) and any(
                isinstance(v, dict) and v.get("issue") != "N/A"
                for v in data.values()
            )

        if not is_meaningful_analysis(analysis_json):
            print("⚠️ First analysis was empty or unhelpful. Retrying once...")
            analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)

        if "error" in analysis_json:
            self.feedback_display.setText(f"❌ Error: {analysis_json['error']}")
            return

        swing_analysis.save_analysis(swing_data["id"], analysis_json)
        self.handle_analysis_result(analysis_json)



    def handle_analysis_result(self, analysis_json):
        if not analysis_json or "error" in analysis_json:
            self.feedback_display.setText("⚠️ Error analyzing swing. Please try again.")
            self.radar_chart.hide()
            return

        feedback_entries = []
        radar_metrics = {}
        for metric, data in analysis_json.items():
            if data.get("severity", 0) > 0 and data.get("issue") != "N/A":
                feedback_entries.append(f"""
<b>{metric.replace("_", " ").title()} - Grade: {data["severity"]}</b><br>
<i>Issue:</i> {data["issue"]}<br>
<i>Description:</i> {data["description"]}<br>
<i>Drill:</i> {data["drill"]}<br><br>
""")
            if data.get("severity") and isinstance(data["severity"], (int, float)):
                radar_metrics[metric] = data["severity"]

        if not feedback_entries:
            self.feedback_display.setText("<i>No issues detected.</i>")
        else:
            self.feedback_display.setText("".join(feedback_entries))

        if radar_metrics:
            self.radar_chart.update_chart(analysis_json)
            self.radar_chart.show()
        else:
            self.radar_chart.hide()

    def update_trend_chart(self):
        selected_metric = self.metric_selector.currentText()
        self.trend_chart.update_chart(selected_metric)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = SwingAnalysisGUI()
    gui.show()
    sys.exit(app.exec_())