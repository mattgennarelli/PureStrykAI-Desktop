from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

class SwingAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("PureStrykAI Desktop")
        layout = QVBoxLayout()
        
        self.label = QLabel("Swing Analysis Dashboard")
        layout.addWidget(self.label)
        
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication([])
    window = SwingAnalyzerGUI()
    window.show()
    app.exec_()
