from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QComboBox
from visualization import plot_latest_swing_radar, plot_swing_trend  # Import radar chart function
import sys
import swing_analysis

class SwingAnalysisGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PureStrykAI Swing Analysis")
        self.layout = QVBoxLayout(self)

        self.analyze_button = QPushButton("Analyze Latest Swing", self)
        self.analyze_button.clicked.connect(self.run_analysis)
        self.layout.addWidget(self.analyze_button)

        self.radar_button = QPushButton("Show Radar Chart", self)
        self.radar_button.clicked.connect(plot_latest_swing_radar)
        self.layout.addWidget(self.radar_button)

        self.metric_dropdown = QComboBox(self)
        self.metric_dropdown.addItems(["club_speed", "ball_speed", "spin_rate", "club_path", 
                                    "face_angle", "attack_angle", "launch_angle", "apex", "sidespin"])
        self.layout.addWidget(self.metric_dropdown)

        self.trend_button = QPushButton("Track Progress", self)
        self.trend_button.clicked.connect(self.track_progress)
        self.layout.addWidget(self.trend_button)

        # Explicitly add the missing results_text widget initialization
        self.results_text = QTextEdit(self)
        self.results_text.setReadOnly(True)
        self.layout.addWidget(self.results_text)

    def run_analysis(self):
        swing_data = swing_analysis.fetch_latest_swing()
        prompt = swing_analysis.construct_dynamic_prompt(swing_data)
        analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)
        self.display_analysis(analysis_json)

    def display_analysis(self, analysis_json):
        self.results_text.clear()
        metrics = analysis_json.get('metrics', {})
        for metric, details in metrics.items():
            if details.get('issue', 'N/A') != "N/A":
                issue = details.get('issue', 'N/A')
                description = details.get('description', 'N/A')
                drill = details.get('drill', 'N/A')

                self.results_text.append(f"<b>{metric}</b>")
                self.results_text.append(f"Issue: {issue}")
                self.results_text.append(f"Description: {description}")
                self.results_text.append(f"Recommended Drill: {drill}\n")
    
    def track_progress(self):
        selected_metric = self.metric_dropdown.currentText()
        plot_swing_trend(selected_metric)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = SwingAnalysisGUI()
    gui.show()
    sys.exit(app.exec())
