import sys, uuid, json, traceback, psutil, time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
from datetime import datetime
from plugs import *
from ctypes import byref, c_bool, sizeof, windll
from ctypes.wintypes import BOOL, MSG
from winreg import QueryValueEx, ConnectRegistry, HKEY_CURRENT_USER, OpenKey, KEY_READ
from enum import Enum
import charset_normalizer as chardet

from addit import *

class Ui_MainWindow(object):
    windowLoaded = QtCore.pyqtSignal()
    onKeyPress = QtCore.pyqtSignal(int)

    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(800, 600)
        self.MainWindow.setStyleSheet(open('ui/style/style.qss', 'r').read())

        self.thread = None
        self.recentFiles = eval(open("recent.f", "r+").read()) or []

        self.centralwidget = QtWidgets.QWidget(parent=self.MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.treeView = QtWidgets.QTreeView(parent=self.centralwidget)
        self.treeView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.treeView.setMinimumWidth(150)
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
        
        self.tab.textEdit = TextEdit(parent=self.tab)
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
        newTabAction.setShortcut(QtGui.QKeySequence("Ctrl+N"))

        self.MainWindow.addAction(openFileAction)
        self.MainWindow.addAction(saveFileAction)
        self.MainWindow.addAction(openDirAction)
        self.MainWindow.addAction(openRecentFileAction)
        self.MainWindow.addAction(newTabAction)

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
            self.thread = FileReadThread(file, tab)
            self.thread.chunkRead.connect(tab.textEdit.append)
            self.thread.finishedReading.connect(lambda: self.encodingLabel.setText(encoding))
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
        for idx in reversed(range(self.tabWidget.count())):
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
        dwmapi = windll.LoadLibrary("dwmapi")
        self.__dwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        self.__detect_theme_flag = True
        # self.__initTheme()

        self.setupUi(self)
        self.windowInitialize()
        proxy = WindowProxy(self)
        plugMan = PluginManager("plugins", proxy)
        plugMan.load_plugins()
        self.windowLoaded.emit()

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
