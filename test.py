from PyQt5 import QtWidgets, QtCore, QtGui

class TabBar(QtWidgets.QTabBar):
    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent)

class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, MainWindow=None, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.MainWindow = MainWindow
        self.setMovable(True)  # Включаем перемещение вкладок
        self.tabbar = TabBar(self)
        self.setTabBar(self.tabbar)

    def setMovable(self, movable):
        # Используем стандартный метод для перемещения вкладок
        QtWidgets.QTabWidget.setMovable(self, movable)

    def closeTab(self, index):
        # Закрытие вкладки
        self.removeTab(index)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    tabWidget = TabWidget(MainWindow)
    MainWindow.setCentralWidget(tabWidget)

    # Добавление нескольких вкладок для тестирования
    for i in range(5):
        tabWidget.addTab(QtWidgets.QWidget(), f"Tab {i+1}")

    MainWindow.show()
    sys.exit(app.exec_())
