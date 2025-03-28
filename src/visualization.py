import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from database import fetch_metric_trend_data


class TrendChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, metric, club_type):
        self.figure.clear()

        swing_numbers, values = fetch_metric_trend_data(metric, club_type)

        if not swing_numbers or not values:
            self.canvas.draw()
            return

        ax = self.figure.add_subplot(111)
        ax.plot(swing_numbers, values, marker='o', linestyle='-', color='blue', markersize=8, markerfacecolor='red')
        ax.set_title(f"{metric.replace('_', ' ').title()} (Last {len(swing_numbers)} Swings with {club_type})")
        ax.set_xlabel("Swing #")
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.grid(True)

        self.canvas.draw()
