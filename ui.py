import sys, importlib, json, configparser
from PyQt5 import QtCore, QtGui, QtWidgets
from datetime import datetime
from ctypes import byref, c_bool, sizeof, windll
from ctypes.wintypes import BOOL, MSG
from winreg import QueryValueEx, ConnectRegistry, HKEY_CURRENT_USER, OpenKey, KEY_READ

from addit import *
from api import *

class PluginManager:
    def __init__(self, plugin_directory: str, w):
        self.plugin_directory = plugin_directory
        self.window = w
        self.plugins = []
    
    def load_plugins(self): self._load_plugins()

    def _load_plugins(self):
        try:
            sys.path.insert(0, self.plugin_directory)
            for plugDir in os.listdir(self.plugin_directory):
                if os.path.isdir(os.path.join(self.plugin_directory, plugDir)) and os.path.isfile(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini"):
                    plugInfo = self.window.api.load_ini_file(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini")
                    self.plugins.append(plugInfo)
                    self.window.log += f"\nFound new plugin with info {plugInfo}"
                    self.window.api.regAll()
        finally:
            sys.path.pop(0)
            self.window.api.commandsLoaded.emit()

class Ui_MainWindow(object):
    windowLoaded = QtCore.pyqtSignal()
    onKeyPress = QtCore.pyqtSignal(int)
    sys.path.insert(0, ".")

    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(800, 600)
        self.MainWindow.setStyleSheet(open('ui/style/style.qss', 'r').read())

        self.log = ""

        self.thread = None
        self.recentFiles = eval(open("recent.f", "r+").read()) or []

        self.centralwidget = QtWidgets.QWidget(parent=self.MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.treeView = QtWidgets.QTreeView(parent=self.centralwidget)
        self.treeView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.treeView.setMinimumWidth(150)
        self.treeView.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
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
        self.loadMenuBar()
        self.MainWindow.setMenuBar(self.menubar)
        
        self.encodingLabel = QtWidgets.QLabel("UTF-8")
        self.statusbar = QtWidgets.QStatusBar(parent=self.MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.addPermanentWidget(self.encodingLabel)
        self.MainWindow.setStatusBar(self.statusbar)

        self.loadingOverlay = LoadingOverlay(self.centralwidget)
        self.loadingOverlay.hide()

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self.MainWindow)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.MainWindow.setWindowTitle(_translate("VarTexter2", "VarTexter2"))

    def addTab(self, name: str = "", text: str = "", i: int = -1, editable: bool = True):
        self.tab = QtWidgets.QWidget()
        self.tab.file = None
        self.tab.canSave = True
        self.tabWidget.tabBar().setTabSaved(self.tab, True)
        self.tab.encoding = "UTF-8"
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
        
        self.tab.textEdit.textChanged.connect(self.textChngd)
        self.tab.textEdit.setText(text)
        self.tab.textEdit.setObjectName("textEdit")

        self.verticalLayout.addLayout(self.tab.textEdit.layout)

        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), name or "Untitled")
        self.tabWidget.currentChanged.connect(self.tabChanged)

        return self.tab
    
    def getCurrentTabIndex(self):
        return self.tabWidget.indexOf(self.tabWidget.currentWidget())
    
    def setTabText(self, i, text):
        tab = self.tabWidget.widget(i)
        return self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), text)

    def getTabText(self, i):
        tab = self.tabWidget.widget(i)
        text = tab.textEdit.toHtml()
        return text

    def getTabFile(self, i):
        tab = self.tabWidget.widget(i)
        pass

    def setTabFile(self, i, file):
        tab = self.tabWidget.widget(i)
        tab.file = file
        return tab.file

    def setTab(self, i):
        if i <= -1:
            self.tabWidget.setCurrentIndex(self.tabWidget.count()-1)
        else:
            self.tabWidget.setCurrentIndex(i-1)

    def getTabSaved(self, i):
        tab = self.tabWidget.widget(i)
        return bool(tab in self.tabWidget.tabBar().savedStates)

    def setTabSaved(self, b: bool, i):
        tab = self.tabWidget.widget(i)
        self.tabWidget.tabBar().setTabSaved(tab or self.tabWidget.currentWidget(), b)

    def textChngd(self):
        tab = self.tabWidget.currentWidget()
        if tab:
            self.tabWidget.tabBar().setTabSaved(tab, False)

    def loadMenuBar(self, e=False):
        pass

    def tabChanged(self, index):
        self.MainWindow.setWindowTitle(f"{self.tabWidget.tabText(index)} - VarTexter2")
        if index >= 0: self.encodingLabel.setText(self.tabWidget.widget(index).encoding)

    def dirOpenDialog(self, e=None):
        dlg = QtWidgets.QFileDialog.getExistingDirectory(
            self.treeView,
            caption="VarTexter - Get directory",
        )
        return str(dlg)

    def dirSet(self, dir: str = None):
        dir = dir or self.dirOpenDialog()
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(dir)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(dir))
        self.treeView.doubleClicked.connect(self.fileManDClicked)
    
    def fileManDClicked(self, i):
        if os.path.isfile(self.model.filePath(i)):
            self.openFile([self.model.filePath(i)])

    def logConsole(self):
        if not LogConsole.running:
            self.console = LogConsole()
            self.console.text_edit.append(self.log)
            self.console.show()

    def windowInitialize(self):
        try:
            tabLog = json.load(open("tablog.json", "r+"))
        except json.decoder.JSONDecodeError:
            tabLog = {}
        for tab in tabLog.get("tabs") or []:
            tab = tabLog.get("tabs").get(tab)
            tabc = self.addTab(name=tab.get("name"), text=tab.get("text"))
            tabc.file = tab.get("file") or None
            tabc.canSave = tab.get("canSave")
            cursor = tabc.textEdit.textCursor()
            cursor.setPosition(tab.get("selection")[0])
            cursor.setPosition(tab.get("selection")[1], QtGui.QTextCursor.KeepAnchor)
            tabc.textEdit.setTextCursor(cursor)
        if tabLog.get("activeTab"):
            self.tabWidget.setCurrentIndex(int(tabLog.get("activeTab")))

    def closeEvent(self, e=False):
        recLog = open("recent.f", "w+")
        recLog.truncate(0)
        recLog.write(str(self.recentFiles))
        recLog.close()

        tabLog = open("tablog.json", "a+")
        tabLog.truncate(0)
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
                    "name": self.tabWidget.tabText(idx),
                    "file": getattr(widget, 'file', None),
                    "canSave": getattr(widget, 'canSave', None),
                    "text": widget.textEdit.toHtml(),
                    "selection": [start, end],
                    "modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        tabs = {str(idx): tabs[str(idx)] for idx in range(len(tabs))}
        json.dump(tabsInfo, tabLog)
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

        self.allowedCommands = ["addTab", "dirSet"]

        dwmapi = windll.LoadLibrary("dwmapi")
        self.__dwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        self.__detect_theme_flag = True
        if self.constants["platform"] == "Windows": self.__initTheme()

        self.contextMenu = QtWidgets.QMenu(self)
        self.textContextMenu = QtWidgets.QMenu(self)
        
        self.setupUi(self)
        self.windowInitialize()

        self.pl = PluginManager("plugins", self)
        self.api = VtAPI(self)
        
        self.api.parseMenu(self.api.loadThemes(), self.menuBar())
        self.api.parseMenu(json.load(open("ui/Main.cm", "r+")), self.contextMenu)
        for shortcut in json.load(open("ui/Main.sc", "r+")):
            self.api.create_shortcut(shortcut) 

        self.api.registerCommand("setLastTab")
        self.api.registerCommand("tabText")
        self.api.registerCommand("setTabSaved")
        self.api.registerCommand("setTabText")

        self.pl.load_plugins()


    def __initTheme(self):
        self.__setCurrentWindowsTheme()

    def nativeEvent(self, eventType, message):
        if self.isDetectingThemeAllowed():
            msg = MSG.from_address(message.__int__())
            if msg.message == 26:
                self.__setCurrentWindowsTheme()
        return super().nativeEvent(eventType, message)

    def __setCurrentWindowsTheme(self):
        try:
            root = ConnectRegistry(None, HKEY_CURRENT_USER)
            root_key = OpenKey(HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize', 0, KEY_READ)
            lightThemeValue, regtype = QueryValueEx(root_key, 'AppsUseLightTheme')
            if lightThemeValue == 0 or lightThemeValue == 1:
                self.__dwmSetWindowAttribute(int(self.winId()), DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE.value, byref(c_bool(lightThemeValue == 0)), sizeof(BOOL))
            else:
                raise Exception(f'Unknown value "{lightThemeValue}".')
        except FileNotFoundError:
            print('AppsUseLightTheme not found.')
        except Exception as e:
            print(e)

    def setDarkTheme(self, f: bool):
        self.__dwmSetWindowAttribute(int(self.winId()), DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE.value,
                                     byref(c_bool(f)), sizeof(BOOL))

    def isDetectingThemeAllowed(self):
        return self.__detect_theme_flag

    def allowDetectingTheme(self, f: bool):
        self.__detect_theme_flag = f

    def contextMenuEvent(self, event):
        if self.contextMenu:
            self.contextMenu.exec_(self.mapToGlobal(event.pos()))

    def settheme(self, theme):
        if os.path.isfile(f"ui/style/{theme[0]}"):
            with open(f"ui/style/{theme[0]}", "r") as file:
                self.MainWindow.setStyleSheet(file.read())

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()