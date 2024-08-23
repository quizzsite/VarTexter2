from PyQt5.QtWidgets import QApplication, QDialog, QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt

class LogConsole(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.text_edit.setStyleSheet("background-color: black; color: white;")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.setWindowTitle("Log Console")
        self.setFixedSize(300, 300)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    console = LogConsole()
    console.show()

    console.text_edit.append("This is a test log entry.")
    console.text_edit.append("Another log entry.")

    sys.exit(app.exec_())
