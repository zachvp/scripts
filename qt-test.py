from PyQt6.QtWidgets import QApplication, QWidget
import sys

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("genres")
        
        stylesheet = (
            "background-color : grey;"
        )

        self.setStyleSheet(stylesheet)

app = QApplication(sys.argv)

window = Window()
window.show()

sys.exit(app.exec())