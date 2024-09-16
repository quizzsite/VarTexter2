from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QMenuBar
from PyQt6.QtGui import QAction
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.toggle_action = QAction("Toggle Option", self)
        self.toggle_action.setCheckable(True)

        # Создаем меню и добавляем действие
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Options")
        file_menu.addAction(self.toggle_action)

    def on_toggle(self, checked):
        if checked:
            print("Option is enabled")
        else:
            print("Option is disabled")

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
