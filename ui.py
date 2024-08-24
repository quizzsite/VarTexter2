import sys, importlib, json, configparser
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from datetime import datetime
from ctypes import byref, c_bool, sizeof, windll
from ctypes.wintypes import BOOL, MSG
from winreg import QueryValueEx, ConnectRegistry, HKEY_CURRENT_USER, OpenKey, KEY_READ

from addit import *

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
                    plugInfo = self.window.load_ini_file(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini")
                    self.plugins.append(plugInfo)
                    self.window.log += f"\nFound new plugin with info {plugInfo}"
                    self.window.regAll()
        finally:
            sys.path.pop(0)

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

        self.enSrtc()

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
        self.tab.saved = True
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
        self.checkTabSaved(self.tab)

        return self.tab

    def checkTabSaved(self, tab):
        if tab:
            if tab.saved:
                btn = self.tabWidget.tabBar().tabButton(self.tabWidget.indexOf(tab), QtWidgets.QTabBar.RightSide)
                if btn:
                    btn.setIcon(QtGui.QIcon('ui/res/x-square-fill.svg'))
            else:
                btn = self.tabWidget.tabBar().tabButton(self.tabWidget.indexOf(tab), QtWidgets.QTabBar.RightSide)
                if btn:
                    btn.setIcon(QtGui.QIcon('ui/res/square-fill.svg'))

    def textChngd(self):
        tab = self.tabWidget.currentWidget()
        tab.saved = False
        self.checkTabSaved(tab)

    def loadMenuBar(self, e=False):
        pass

    def tabChanged(self, index):
        self.MainWindow.setWindowTitle(f"{self.tabWidget.tabText(index)} - VarTexter2")
        if index >= 0: self.encodingLabel.setText(self.tabWidget.widget(index).encoding)

    def keyPressEvent(self, event):
        self.onKeyPress.emit(event.key())
        self.MainWindow.keyPressEvent(event)

    def dirOpenDialog(self, e=None):
        dlg = QtWidgets.QFileDialog.getExistingDirectory(
            self.treeView,
            caption="VarTexter - Get directory",
        )
        return str(dlg)

    def openFileDialog(self, e=None):
        dlg = QtWidgets.QFileDialog.getOpenFileNames()
        return dlg

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

    def enSrtc(self):
        openFileAction = QtWidgets.QAction(self.MainWindow)
        openFileAction.setText("Open directory")
        openFileAction.triggered.connect(self.openFile)
        openFileAction.setShortcut(QtGui.QKeySequence("Ctrl+O"))

        saveFileAction = QtWidgets.QAction(self.MainWindow)
        saveFileAction.setText("Save directory")
        saveFileAction.triggered.connect(self.saveFile)
        saveFileAction.setShortcut(QtGui.QKeySequence("Ctrl+S"))

        openDirAction = QtWidgets.QAction(self.MainWindow)
        openDirAction.setText("Open directory")
        openDirAction.triggered.connect(self.dirSet)
        openDirAction.setShortcut(QtGui.QKeySequence("Ctrl+Shift+O"))

        openRecentFileAction = QtWidgets.QAction(self.MainWindow)
        openRecentFileAction.setText("Open directory")
        openRecentFileAction.triggered.connect(self.openRecentFile)
        openRecentFileAction.setShortcut(QtGui.QKeySequence("Ctrl+Shift+T"))

        newTabAction = QtWidgets.QAction(self.MainWindow)
        newTabAction.setText("New tab")
        newTabAction.triggered.connect(self.addTab)
        # newTabAction.setShortcut(QtGui.QKeySequence("Ctrl+N"))

        logConsoleAction = QtWidgets.QAction(self.MainWindow)
        logConsoleAction.setText("Log Console")
        logConsoleAction.triggered.connect(self.logConsole)
        logConsoleAction.setShortcut(QtGui.QKeySequence("Shift+Esc"))

        self.MainWindow.addAction(openFileAction)
        self.MainWindow.addAction(saveFileAction)
        self.MainWindow.addAction(openDirAction)
        self.MainWindow.addAction(openRecentFileAction)
        self.MainWindow.addAction(newTabAction)
        self.MainWindow.addAction(logConsoleAction)

    def logConsole(self):
        if not LogConsole.running:
            self.console = LogConsole()
            self.console.text_edit.append(self.log)
            self.console.show()

    def openRecentFile(self, e=False):
        if len(self.recentFiles) > 0:
            self.openFile([self.recentFiles[-1]])
            self.recentFiles.remove(self.recentFiles[-1])
            recLog = open("recent.f", "w+")
            recLog.truncate(0)
            recLog.write(str(self.recentFiles))
            recLog.close()

    def openFile(self, filePath=None, encoding=None):
        if not filePath:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File", "", "All Files (*);;Text Files (*.txt)")
            if not filePath:
                return
        for file in filePath:
            encoding = encoding or 'utf-8'
            tab = self.addTab(name=file, editable=True)
            self.tabWidget.setCurrentIndex(self.tabWidget.count()-1)
            self.thread = FileReadThread(file, tab)
            self.thread.chunkRead.connect(tab.textEdit.append)
            self.thread.finishedReading.connect(lambda: self.encodingLabel.setText(encoding))
            self.thread.finished.connect(self.thread.stop)
            self.thread.start()

    def saveFile(self):
        tab = self.tabWidget.currentWidget()
        if tab.canSave:
            self.text = tab.textEdit.toHtml()
            if not tab.file:
                tab.file = QtWidgets.QFileDialog.getSaveFileName()[0]
            self.thread = FileWriteThread(tab, tab.textEdit.toHtml())
            self.thread.start()   
        self.checkTabSaved(tab)

    def saveAsFile(self):
        tab = self.tabWidget.currentWidget()
        if tab.canSave:
            self.text = tab.textEdit.toHtml()
            tab.file = QtWidgets.QFileDialog.getSaveFileName()[0]
            self.thread = FileWriteThread(tab, tab.textEdit.toHtml())
            self.thread.start()   

    def windowInitialize(self):
        tabLog = json.load(open("tablog.json", "r+"))
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

        dwmapi = windll.LoadLibrary("dwmapi")
        self.__dwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        self.__detect_theme_flag = True
        if self.constants["platform"] == "Windows": self.__initTheme()

        self.contextMenu = QtWidgets.QMenu(self)
        self.textContextMenu = QtWidgets.QMenu(self)
        
        self.setupUi(self)
        self.windowInitialize()
        self.menu_map = {}
        self.commands = {}

        self.pl = PluginManager("plugins", self)
        
        self.parse_menu(self.loadThemes(), self.menuBar())
        self.parse_menu(json.load(open("ui/Main.cm", "r+")), self.contextMenu)
        for shortcut in json.load(open("ui/Main.sc", "r+")):
            self.create_shortcut(shortcut) 

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


    def load_ini_file(self, ini_path):
        self.ini_path = ini_path
        config = configparser.ConfigParser()
        config.read(self.ini_path)

        self.name = config.get('DEFAULT', 'name', fallback='Unknown Plugin')

        self.version = config.get('DEFAULT', 'version', fallback='1.0')

        self.main_script = config.get('DEFAULT', 'main', fallback='')

        self.plugInfo = {"name": self.name, "version": self.version, "path": ini_path, "main": self.main_script}

        self.cm = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'cm', fallback=''))) if config.get('DEFAULT', 'cm', fallback='') else ""

        self.tcm = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'tcm', fallback=''))) if config.get('DEFAULT', 'tcm', fallback='') else ""
    
        self.mb = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'mb', fallback=''))) if config.get('DEFAULT', 'mb', fallback='') else ""
    
        self.sc = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'sc', fallback=''))) if config.get('DEFAULT', 'sc', fallback='') else ""
    
        return self.plugInfo

    def regAll(self):
        if self.mb:
            self.parse_menu(json.load(open(self.mb, "r+")), self.menuBar(), pluginPath=self.ini_path)
            self.plugInfo["mb"] = self.mb

        if self.cm:
            self.parse_menu(json.load(open(self.cm, "r+")), self.contextMenu, pluginPath=self.ini_path)
            self.plugInfo["cm"] = self.cm

        if self.tcm:
            self.parse_menu(json.load(open(self.tcm, "r+")), self.textContextMenu, pluginPath=self.ini_path)
            self.plugInfo["tcm"] = self.tcm

        if self.sc:
            for shortcut in json.load(open(self.sc, "r+")):
                self.create_shortcut(shortcut)            
            self.plugInfo["sc"] = self.sc

    def contextMenuEvent(self, event):
        if self.contextMenu:
            self.contextMenu.exec_(self.mapToGlobal(event.pos()))

    def create_shortcut(self, shortcut_info):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        args = shortcut_info.get("args", {})
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = QtWidgets.QAction(self)
        action.setShortcut(key_sequence)
        self.registerCommand(command)
        action.triggered.connect(lambda: self.execute_command(command, args))
        self.addAction(action)

    def parse_menu(self, data, parent, pluginPath=None):
        if isinstance(data, dict):
            data = [data]

        for item in data:
            menu_id = item.get('id')
            if menu_id:
                menu = self.menu_map.setdefault(menu_id, QtWidgets.QMenu(item.get('caption', 'Unnamed'), self))
                parent.addMenu(menu)
                if 'children' in item:
                    self.parse_menu(item['children'], menu, pluginPath)
            else:
                if 'children' in item:
                    submenu = QtWidgets.QMenu(item.get('caption', 'Unnamed'), self)
                    self.parse_menu(item['children'], submenu)
                    parent.addMenu(submenu)
                else:
                    if item.get('caption') == "-":
                        parent.addSeparator()
                    else:
                        action = QtWidgets.QAction(item.get('caption', 'Unnamed'), self)
                        if 'command' in item:
                            self.registerCommand(item['command'], pluginPath)
                            action.triggered.connect(lambda checked, cmd=item['command'], args=item.get('args', {}): self.execute_command(cmd, args))
                        parent.addAction(action)
                        if 'shortcut' in item:
                            action.setShortcut(QtGui.QKeySequence(item['shortcut']))
    def findThemeMenu(self, menu):
        if menu:
            if menu.get("id") == "themes":
                return menu
            for c in menu.get("children", []):
                found = self.findThemeMenu(c)
                if found:
                    return found
        return None
    def settheme(self, theme):
        if os.path.isfile(f"ui/style/{theme[0]}"):
            with open(f"ui/style/{theme[0]}", "r") as file:
                self.MainWindow.setStyleSheet(file.read())

    def loadThemes(self):
        if os.path.isdir("ui/style"):
            with open("ui/Main.mb", "r") as file:
                menus = json.load(file)

            for menu in menus:
                themeMenu = self.findThemeMenu(menu)
                if themeMenu:
                    childrens = themeMenu.get("children", [])
                    themeMenu["children"] = [{"caption": theme, "command": f"settheme {theme}"} for theme in os.listdir("ui/style")]
                    break
        return menus

    def execute_command(self, command, *args):
        commandnargs = command.split()
        c = self.commands.get(commandnargs[0])
        if c:
            try:
                args = commandnargs[1:]
                c.get("command")(args)
            except Exception as e:
                self.log += f"\nFound error in {command} - {e}.\nInfo: {c}"
    def registerCommand(self, command, pluginPath=None):
        commandN = command.split()[0]
        if pluginPath:
            for plugin in self.pl.plugins:
                if plugin.get("path") == pluginPath:
                    self.command = {}
                    sys.path.insert(0, os.path.dirname(plugin.get("path")))
                    main_module = plugin.get("main")
                    if main_module.endswith('.py'):
                        main_module = main_module[:-3]
                    try:
                        plug = importlib.import_module(main_module)
                        command = getattr(plug, commandN)
                        self.command["command"] = command
                        self.command["plugin"] = plug
                        self.commands[commandN] = self.command
                    except Exception as e:
                        self.log += f"\nFound error in {main_module} - {e}"
        else:
            self.command = {}
            command = getattr(self, commandN)
            self.command["command"] = command
            self.command["plugin"] = None
            self.commands[commandN] = self.command
            
def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()