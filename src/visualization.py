import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from database import fetch_metric_trend_data


class RadarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, analysis_json):
        self.figure.clear()

        if not analysis_json:
            self.canvas.draw()
            return

        metrics = list(analysis_json.keys())
        values = [min(100, max(0, analysis_json[m].get("severity", 0))) for m in metrics]

        values += values[:1]
        labels = metrics + [metrics[0]]

        angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]

        ax = self.figure.add_subplot(111, polar=True)
        ax.plot(angles, values, linewidth=2, linestyle='solid', color='black')
        ax.fill(angles, values, color='orange', alpha=0.5)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_ylim(0, 100)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_title("Swing Performance - Metrics")

        self.canvas.draw()

class TrendChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, metric):
        self.figure.clear()

        timestamps, values = fetch_metric_trend_data(metric)

        if not timestamps or not values:
            self.canvas.draw()
            return

        ax = self.figure.add_subplot(111)
        ax.plot(timestamps, values, marker='o', linestyle='-', color='blue', markersize=8, markerfacecolor='red')
        ax.set_title(f"{metric.replace('_', ' ').title()} Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.grid(True)
        self.figure.autofmt_xdate()

        self.canvas.draw()