import sys, json, os
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
        self.treeView.setObjectName("treeWidget")
        
        self.treeSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.horizontalLayout.addWidget(self.treeSplitter)
        
        self.tabWidget = TabWidget(parent=self.centralwidget, MainWindow=self.MainWindow)
        self.treeSplitter.addWidget(self.treeView)
        self.treeSplitter.addWidget(self.tabWidget)

        self.MainWindow.setCentralWidget(self.centralwidget)
        
        self.menubar = QtWidgets.QMenuBar(parent=self.MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menuBar")

        self.MainWindow.setMenuBar(self.menubar)
        
        self.encodingLabel = QtWidgets.QLabel("UTF-8")
        self.statusbar = QtWidgets.QStatusBar(parent=self.MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.addPermanentWidget(self.encodingLabel)
        self.MainWindow.setStatusBar(self.statusbar)

        self.api = VtAPI(self.MainWindow)

        self.tabWidget.currentChanged.connect(self.api.tabChngd)

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
        self.frame.setObjectName("tabFrame")
        self.verticalLayout.addWidget(self.frame)
        
        self.tab.textEdit = TextEdit(self.MainWindow)
        self.tab.textEdit.setReadOnly(False)
        
        self.tab.textEdit.setText(text)
        self.tab.textEdit.setObjectName("textEdit")

        self.verticalLayout.addLayout(self.tab.textEdit.layout)

        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), name or "Untitled")
        self.api.setTab(-1)

        self.tab.textEdit.textChanged.connect(self.api.textChngd)
        self.tab.textEdit.document().contentsChanged.connect(self.api.textChngd)

    def closeTab(self, i: int = None):
        if not i:
            i = self.api.currentTabIndex()
        self.tabWidget.closeTab(i)

    def logConsole(self, checked=None):
        if checked:
            self.console = ConsoleWidget(self.MainWindow)
            self.console.textEdit.append(self.logger.log)
            self.MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.console)
        elif checked == False:
            self.console.close()
        else:
            if not self.console:
                self.logConsole(checked=True)
            else:
                self.console.deleteLater()
                self.console = None

    def settings(self):
        self.settFile = open(os.path.join(os.getcwd(), 'ui/Main.settings'), 'r+', encoding='utf-8')
        self.settData = json.load(self.settFile)
        self.packageDirs = self.settData.get("packageDirs")
        if self.packageDirs:
            self.packageDirs = StaticInfo.replacePaths(self.packageDirs.get(StaticInfo.get_platform()))
            self.themesDir = StaticInfo.replacePaths(os.path.join(self.packageDirs, "Themes"))
            self.pluginsDir = StaticInfo.replacePaths(os.path.join(self.packageDirs, "Plugins"))
            self.uiDir = StaticInfo.replacePaths(os.path.join(self.packageDirs, "Ui"))
        self.MainWindow.appName = self.settData.get("appName")
        self.MainWindow.__version__ = self.settData.get("apiVersion")
        self.MainWindow.remindOnClose = self.settData.get("remindOnClose")
        self.mb = StaticInfo.replacePaths(os.path.join(self.packageDirs, self.settData.get("mb")))
        self.cm = StaticInfo.replacePaths(os.path.join(self.packageDirs, self.settData.get("cm")))
        self.sc = StaticInfo.replacePaths(os.path.join(self.packageDirs, self.settData.get("sc")))

    def settingsHotKeys(self):
        if os.path.isfile(self.sc):
            openFile = self.api.getCommand("openFile")
            if openFile:
                openFile.get("command")([self.sc])
            else:
                QtWidgets.QMessageBox.warning(self.MainWindow, self.MainWindow.appName+" - Warning", f"Open file function not found. You can find file at {self.sc}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        openFile = self.api.getCommand("openFile")
        if openFile:
            openFile.get("command")(files)
        else:
            QtWidgets.QMessageBox.warning(self.MainWindow, self.MainWindow.appName+" - Warning", f"Open file function not found. Check your Open&Save plugin at {os.path.join(self.pluginsDir, 'Open&Save')}")

    def windowInitialize(self):
        [os.makedirs(dir) for dir in [self.themesDir, self.pluginsDir, self.uiDir] if not os.path.isdir(dir)]
        tabLog = {}
        stateFile = os.path.join(self.packageDirs, 'data.msgpack')
        try:
            if os.path.isfile(stateFile):
                with open(stateFile, 'rb') as f:
                    packed_data = f.read()
                    tabLog = msgpack.unpackb(packed_data, raw=False)
                    for tab in tabLog.get("tabs") or []:
                        tab = tabLog.get("tabs").get(tab)
                        self.addTab(name=tab.get("name"), text=tab.get("text"), file=tab.get("file"), canSave=tab.get("canSave"))
                        self.api.textChangeEvent(self.api.currentTabIndex())
                        self.MainWindow.setWindowTitle(f"{self.MainWindow.tabWidget.tabText(self.api.currentTabIndex())} - VarTexter2")
                        self.api.setTextSelection(self.api.currentTabIndex(), tab.get("selection")[0], tab.get("selection")[1])
                    if tabLog.get("activeTab"):
                        self.tabWidget.setCurrentIndex(int(tabLog.get("activeTab")))
        except ValueError:
            self.logger.log += f"\nFailed to restore window state. No file found at {stateFile}"
            open(stateFile)

    def closeEvent(self, e: QtCore.QEvent):
        self.saveWState()
        self.api.windowClosed.emit()

        e.accept()

    def saveWState(self):
        tabsInfo = {}
        tabs = tabsInfo["tabs"] = {}
        i = self.api.currentTabIndex()
        tabsInfo["activeTab"] = str(i)
        stateFile = os.path.join(self.packageDirs, 'data.msgpack')
        for idx in range(self.tabWidget.count()):
            widget = self.tabWidget.widget(idx)
            if widget and isinstance(widget, QtWidgets.QWidget):
                cursor = self.api.getTextCursor(i)
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
        if os.path.isfile(stateFile):
            mode = 'wb'
        else:
            mode = 'ab'
        with open(stateFile, mode) as f:
            packed_data = msgpack.packb(tabsInfo, use_bin_type=True)
            f.write(packed_data)
        self.settFile.close()

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.constants = {
            "platform": StaticInfo.get_platform(),
            "basedir": StaticInfo.get_basedir(),
            "filedir": StaticInfo.get_filedir(__file__),
            "username": os.getlogin(),
        }

        self.contextMenu = QtWidgets.QMenu(self)
        self.textContextMenu = QtWidgets.QMenu(self)
        
        self.setupUi(self)
        self.windowInitialize()

        self.pl = PluginManager(self.pluginsDir, self)

        self.api.loadThemes()
        self.api.registerCommand("setTheme")
        self.api.registerCommand("settingsHotKeys")
        self.api.executeCommand("setTheme", ["style.qss"])

        if self.mb and os.path.isfile(self.mb):        self.api.parseMenu(json.load(open(self.mb, "r+")), self.menuBar())
        if self.cm and os.path.isfile(self.cm):        self.api.parseMenu(json.load(open(self.cm, "r+")), self.contextMenu)
        if self.sc and os.path.isfile(self.sc):
            for shortcut in json.load(open(self.sc, "r+")):
                self.api.createShortcut(shortcut) 

        self.pl.load_plugins()

    def setTheme(self, theme):
        os.chdir(self.themesDir)
        themePath = os.path.join(self.themesDir, theme[0])
        if os.path.isfile(themePath):
            self.setStyleSheet(open(themePath, "r+").read())
        os.chdir(".")
    
    def argvParse(self):
        argv = sys.argv[1:]

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()