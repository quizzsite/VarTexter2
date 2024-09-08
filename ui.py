import sys, json
from PyQt6 import QtCore, QtWidgets
from datetime import datetime
import msgpack

from addit import *
from api import *

class Logger:
    def __init__(self, w):
        self._log = ""
        self.__window = w

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, value):
        self._log = value
        if self.__window.console:
            self.__window.console.textEdit.clear()
            self.__window.console.textEdit.append(value)

class Ui_MainWindow(object):
    sys.path.insert(0, ".")

    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.settings()
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.setWindowTitle(self.MainWindow.appName)
        self.MainWindow.resize(800, 600)

        self.console = None

        self.logger = Logger(self.MainWindow)

        self.centralwidget = QtWidgets.QWidget(parent=self.MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.treeView = QtWidgets.QTreeView(parent=self.centralwidget)
        self.treeView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.treeView.setMinimumWidth(150)
        self.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.treeView.setMaximumWidth(300)
        self.treeView.setObjectName("treeView")
        
        self.treeSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.horizontalLayout.addWidget(self.treeSplitter)
        
        self.tabWidget = TabWidget(parent=self.centralwidget, MainWindow=self.MainWindow)
        self.tabWidget.setObjectName("tabWidget")
        self.treeSplitter.addWidget(self.treeView)
        self.treeSplitter.addWidget(self.tabWidget)

        self.widget = QtWidgets.QWidget(parent=self.centralwidget)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.MainWindow.setCentralWidget(self.centralwidget)
        
        self.menubar = QtWidgets.QMenuBar(parent=self.MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")

        self.MainWindow.setMenuBar(self.menubar)
        
        self.encodingLabel = QtWidgets.QLabel("UTF-8")
        self.statusbar = QtWidgets.QStatusBar(parent=self.MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.addPermanentWidget(self.encodingLabel)
        self.MainWindow.setStatusBar(self.statusbar)

        self.api = VtAPI(self.MainWindow)
        QtCore.QMetaObject.connectSlotsByName(self.MainWindow)

    def addTab(self, name: str = "", text: str = "", i: int = -1, file=None, canSave=True, encoding="UTF-8"):
        self.tab = QtWidgets.QWidget()
        self.tab.file = file
        self.tab.canSave = canSave
        self.tabWidget.tabBar().setTabSaved(self.tab, True)
        self.tab.encoding = encoding
        self.tab.setObjectName("tab")
        
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.frame = QtWidgets.QFrame(parent=self.tab)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout.addWidget(self.frame)
        
        self.tab.textEdit = TextEdit(self.MainWindow)
        self.tab.textEdit.setReadOnly(False)
        
        self.tab.textEdit.setText(text)
        self.tab.textEdit.setObjectName("textEdit")

        self.verticalLayout.addLayout(self.tab.textEdit.layout)

        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), name or "Untitled")
        self.tabWidget.currentChanged.connect(self.api.tabChngd)

    def logConsole(self):
        if not self.console:
            self.console = ConsoleWidget(self.MainWindow)
            self.console.textEdit.append(self.logger.log)
            self.MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.console)

    def settings(self):
        with open('ui/Main.settings', 'r', encoding='utf-8') as f:
            data = json.load(f)
            f.close()
        self.packageDirs = data.get("packageDirs")
        if self.packageDirs:
            self.packageDirs = StaticInfo.replacePaths(self.packageDirs.get(StaticInfo.get_platform()))
            self.themesDir = StaticInfo.replacePaths(os.path.join(self.packageDirs, "Themes"))
            self.pluginsDir = StaticInfo.replacePaths(os.path.join(self.packageDirs, "Plugins"))
        self.MainWindow.appName = data.get("appName")
        self.MainWindow.__version__ = data.get("apiVersion")
        self.remindOnClose = data.get("remindOnClose")
        self.mb = StaticInfo.replacePaths(os.path.join(self.packageDirs, data.get("mb")))
        self.cm = StaticInfo.replacePaths(os.path.join(self.packageDirs, data.get("cm")))
        self.sc = StaticInfo.replacePaths(os.path.join(self.packageDirs, data.get("sc")))

    def windowInitialize(self):
        tabLog = {}
        try:
            with open('data.msgpack', 'rb') as f:
                packed_data = f.read()
                tabLog = msgpack.unpackb(packed_data, raw=False)
        except ValueError:
            self.logger.log += "\nFailed to restore window state"
        for tab in tabLog.get("tabs") or []:
            tab = tabLog.get("tabs").get(tab)
            self.addTab(name=tab.get("name"), text=tab.get("text"), file=tab.get("file"), canSave=tab.get("canSave"))
            self.api.textChangeEvent(self.api.currentTabIndex())
            self.MainWindow.setWindowTitle(f"{self.MainWindow.tabWidget.tabText(self.api.currentTabIndex())} - VarTexter2")
            self.api.setTextSelection(self.api.currentTabIndex(), tab.get("selection")[0], tab.get("selection")[1])
        if tabLog.get("activeTab"):
            self.tabWidget.setCurrentIndex(int(tabLog.get("activeTab")))

    def closeEvent(self, e=False):
        tabsInfo = {}
        tabs = tabsInfo["tabs"] = {}
        tabsInfo["activeTab"] = str(self.tabWidget.currentIndex())
        for idx in range(self.tabWidget.count()):
            widget = self.tabWidget.widget(idx)
            if widget and isinstance(widget, QtWidgets.QWidget):
                cursor = widget.textEdit.textCursor()
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                tabs[str(idx)] = {
                    "name": self.api.getTabTitle(idx),
                    "file": self.api.getTabFile(idx),
                    "canSave": self.api.getTabCanSave(idx),
                    "text": self.api.getTabText(idx),
                    "selection": [start, end],
                    "modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        tabs = {str(idx): tabs[str(idx)] for idx in range(len(tabs))}
        with open('data.msgpack', 'wb') as f:
            packed_data = msgpack.packb(tabsInfo, use_bin_type=True)
            f.write(packed_data)

        self.api.windowClosed.emit()

        e.accept()

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.constants = {
            "platform": StaticInfo.get_platform(),
            "basedir": StaticInfo.get_basedir(),
            "filedir": StaticInfo.get_filedir(__file__),
            "username": os.getlogin()
        }

        self.contextMenu = QtWidgets.QMenu(self)
        self.textContextMenu = QtWidgets.QMenu(self)
        
        self.setupUi(self)
        self.windowInitialize()

        self.pl = PluginManager(self.pluginsDir, self)

        self.api.loadThemes()
        self.api.registerCommand("setTheme")
        self.api.executeCommand("setTheme style.qss")
        
        if self.mb:        self.api.parseMenu(json.load(open(self.mb, "r+")), self.menuBar())
        if self.cm:        self.api.parseMenu(json.load(open(self.cm, "r+")), self.contextMenu)
        if self.sc:
            for shortcut in json.load(open(self.sc, "r+")):
                self.api.createShortcut(shortcut) 

        self.pl.load_plugins()

    def contextMenuEvent(self, event):
        if self.contextMenu:
            self.contextMenu.exec(self.mapToGlobal(event.pos()))

    def setTheme(self, theme):
        themePath = os.path.join(self.themesDir, theme[0])
        if os.path.isfile(themePath):
            self.setStyleSheet(open(themePath, "r+").read())

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()