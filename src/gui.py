import sys
import json
import swing_analysis
from visualization import TrendChart
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QComboBox,
    QHBoxLayout, QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class SwingAnalysisGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PureStrykAI Swing Analysis")
        self.setMinimumWidth(1000)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Scroll area for entire window content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        # Analyze button
        self.analyze_button = QPushButton("Analyze Latest Swing")
        self.analyze_button.clicked.connect(self.run_analysis)
        self.scroll_layout.addWidget(self.analyze_button)

        # Feedback section title
        self.feedback_label = QLabel("🤖 <b>AI Feedback & Recommendations</b>")
        self.feedback_label.setStyleSheet("font-size: 16px; margin-top: 10px;")
        self.scroll_layout.addWidget(self.feedback_label)

        # Feedback table
        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(5)
        self.feedback_table.setHorizontalHeaderLabels(["Metric", "Value", "Status", "Description", "Drill"])
        self.feedback_table.verticalHeader().setVisible(False)

        # Disable scrollbars on table
        self.feedback_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.feedback_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Resize behavior
        self.feedback_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        header = self.feedback_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        self.scroll_layout.addWidget(self.feedback_table)

        # Metric selector + track button
        metric_layout = QHBoxLayout()
        self.metric_label = QLabel("Select Metric:")
        self.metric_selector = QComboBox()
        self.trend_button = QPushButton("Track Progress")
        self.trend_button.clicked.connect(self.update_trend_chart)

        metric_layout.addWidget(self.metric_label)
        metric_layout.addWidget(self.metric_selector)
        metric_layout.addWidget(self.trend_button)
        self.scroll_layout.addLayout(metric_layout)

        # Trend chart
        self.trend_chart = TrendChart()
        self.trend_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.scroll_layout.addWidget(self.trend_chart)

        # Finalize scroll area
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
            self._show_message_table("⚠️ No swing data found.")
            return

        prompt = swing_analysis.construct_dynamic_prompt(swing_data)
        analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)

        def is_meaningful_analysis(data):
            return isinstance(data, dict) and any(
                isinstance(v, dict) and v.get("issue") != "N/A"
                for v in data.values()
            )

        if not is_meaningful_analysis(analysis_json):
            print("⚠️ First analysis was empty. Retrying...")
            analysis_json = swing_analysis.analyze_swing_with_gpt(prompt)

        if "error" in analysis_json:
            self._show_message_table(f"❌ Error: {analysis_json['error']}")
            return

        swing_analysis.save_analysis(swing_data["id"], analysis_json)
        self.display_feedback_table(swing_data, analysis_json)

    def display_feedback_table(self, swing_data, analysis_json):
        metrics_data = analysis_json.get("metrics", analysis_json)
        rows = []

        for metric, data in metrics_data.items():
            metric_name = metric.replace("_", " ").title()
            def match_metric_key(gpt_key, data_dict):
                simplified = lambda s: s.replace("_", "").replace(" ", "").lower()
                gpt_simplified = simplified(gpt_key)
                for k in data_dict:
                    if simplified(k) == gpt_simplified:
                        return data_dict[k]
                return "N/A"

            value = match_metric_key(metric, swing_data)

            severity = data.get("severity", 0)
            description = data.get("description", "")
            drill = data.get("drill", "")
            rows.append((metric_name, str(value), severity, description, drill))

        self.feedback_table.setRowCount(len(rows))

        for i, (metric, value, severity, desc, drill) in enumerate(rows):
            self.feedback_table.setItem(i, 0, self._text_item(metric))
            self.feedback_table.setItem(i, 1, self._text_item(value))
            self.feedback_table.setCellWidget(i, 2, self._status_icon(severity, drill))
            self.feedback_table.setItem(i, 3, self._text_item(desc))
            self.feedback_table.setItem(i, 4, self._text_item(drill))

        self.feedback_table.resizeRowsToContents()
        total_height = self.feedback_table.horizontalHeader().height()
        for row in range(self.feedback_table.rowCount()):
            total_height += self.feedback_table.rowHeight(row)
        self.feedback_table.setMinimumHeight(total_height)

    def update_trend_chart(self):
        selected_metric = self.metric_selector.currentText()
        self.trend_chart.update_chart(selected_metric)

    def _text_item(self, text):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        return item

    def _status_icon(self, severity, drill):
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        if drill == "N/A":
            icon = "resources/check.png"
        elif severity > 65:
            icon = "resources/warning.png"
        else:
            icon = "resources/cross.png"
        pixmap = QPixmap(icon).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pixmap)
        return label

    def _show_message_table(self, message):
        self.feedback_table.setRowCount(1)
        self.feedback_table.setColumnCount(1)
        self.feedback_table.setHorizontalHeaderLabels(["Info"])
        self.feedback_table.setItem(0, 0, QTableWidgetItem(message))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = SwingAnalysisGUI()
    gui.show()
    sys.exit(app.exec_())
