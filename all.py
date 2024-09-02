import uuid, platform, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from enum import Enum
import charset_normalizer as chardet

class DWMWINDOWATTRIBUTE(Enum):
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20

class LogConsole(QtWidgets.QDialog):
    running = False
    def __init__(self):
        super().__init__()

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.text_edit.setStyleSheet("background-color: black; color: white;")
        running = True

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.setWindowTitle("Log Console")
        self.setFixedSize(300, 300)
    def closeEvent(self, e):
        running = False

class LineNumberWidget(QtWidgets.QTextBrowser):
    def __init__(self, widget):
        super().__init__()
        self.target_widget = widget
        self.__initUi()

    def __initUi(self):
        self.__size = int(self.target_widget.font().pointSizeF())
        self.__styleInit()

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.target_widget.verticalScrollBar().valueChanged.connect(self.__changeLineWidgetScrollAsTargetedWidgetScrollChanged)
        self.target_widget.document().contentsChanged.connect(self.updateLineNumbers)

        self.updateLineNumbers()

    def __changeLineWidgetScrollAsTargetedWidgetScrollChanged(self, v):
        self.verticalScrollBar().setValue(v)

    def updateLineNumbers(self):
        block = self.target_widget.document().firstBlock()
        line_count = 0
        self.clear()

        while block.isValid():
            line_count += self.target_widget.document().documentLayout().blockBoundingRect(block).height() / self.__size
            block = block.next()
        
        for i in range(int(line_count)):
            self.append(str(i + 1))

    def setFontSize(self, s: float):
        self.__size = int(s)
        self.__styleInit()
        self.updateLineNumbers()

    def __styleInit(self):
        self.__style = f'''
                       QTextBrowser 
                       {{ 
                       background: transparent; 
                       border: none; 
                       color: #AAA; 
                       font: {self.__size}pt;
                       margin: 0px;
                       padding: 0px;
                       line-height: {self.__size}px;
                       }}
                       '''
        self.setStyleSheet(self.__style)
        self.setFixedWidth(self.__size * 5)


class MiniMap(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setFixedWidth(150)
        self.setTextInteractionFlags (QtCore.Qt.NoTextInteraction) 
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.setCursor(QtCore.Qt.ArrowCursor)
        self._isDragging = False
        self.setStyleSheet("QTextEdit { selection-background-color: rgba(255, 255, 255, 50); selection-color: black; }")

    def setTextEdit(self, text_edit):
        self.text_edit = text_edit
        self.setHtml(self.text_edit.toHtml())
        self.text_edit.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.text_edit.verticalScrollBar().rangeChanged.connect(self.update_minimap)
        self.text_edit.textChanged.connect(self.update_minimap)
        self.setFontPointSize(1)
        self.update_minimap()
        self.viewport().update()

    def contextMenuEvent(self, event): event.ignore()

    @pyqtSlot()
    def sync_scroll(self):
        max_value = self.text_edit.verticalScrollBar().maximum()
        if max_value != 0:
            value = self.text_edit.verticalScrollBar().value()
            ratio = value / max_value
            self.verticalScrollBar().setValue(int(ratio * self.verticalScrollBar().maximum()))
        self.viewport().update()

    @pyqtSlot()
    def update_minimap(self):
        self.setPlainText(self.text_edit.toPlainText())
        self.sync_scroll()
        self.viewport().update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._isDragging = True
            self.sync_scroll_from_position(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._isDragging:
            self.sync_scroll_from_position(event.pos())
            self.textCursor().clearSelection()
        super().mouseMoveEvent(event)
        self.textCursor().clearSelection()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.textCursor().clearSelection()
            self._isDragging = False
        super().mouseReleaseEvent(event)

    def sync_scroll_from_position(self, pos):
        if self.viewport().height() != 0:
            ratio = pos.y() / self.viewport().height()
            value = int(ratio * self.text_edit.verticalScrollBar().maximum())
            self.text_edit.verticalScrollBar().setValue(value)
            self.textCursor().clearSelection()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        scroll_bar = self.text_edit.verticalScrollBar()
        scroll_bar.setValue(int(scroll_bar.value() - delta / 1.5))

    def resizeEvent(self, event):
        self.update_minimap()
        super().resizeEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.text_edit is None:
            return

        viewport_rect = self.text_edit.viewport().rect()
        content_rect = self.text_edit.document().documentLayout().blockBoundingRect(self.text_edit.document().firstBlock()).united(
            self.text_edit.document().documentLayout().blockBoundingRect(self.text_edit.document().lastBlock())
        )

        viewport_height = self.viewport().height()
        content_height = content_rect.height()
        if content_height == 0:
            return
        scale_factor = viewport_height / content_height

        visible_rect_height = viewport_rect.height() * scale_factor
        visible_rect_top = self.text_edit.verticalScrollBar().value() * scale_factor

        visible_rect = QtCore.QRectF(
            0,
            visible_rect_top,
            self.viewport().width(),
            visible_rect_height
        )

        painter = QtGui.QPainter(self.viewport())
        painter.setBrush(QtGui.QColor(0, 0, 255, 50))
        painter.setPen(QtGui.QColor(0, 0, 255))
        painter.drawRect(visible_rect)


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.lineWidget = LineNumberWidget(self)

        self.minimap = MiniMap(self)
        self.minimap.setTextEdit(self)

        self.layout = QtWidgets.QHBoxLayout()
        # self.layout.addWidget(self.lineWidget)
        self.layout.addWidget(self)

        self.minimap_scroll_area = QtWidgets.QScrollArea()
        self.minimap_scroll_area.setWidget(self.minimap)
        self.minimap_scroll_area.setFixedWidth(150)
        self.minimap_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.minimap_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.layout.addWidget(self.minimap_scroll_area)

    def contextMenu(self, pos):
        self.mw.textContextMenu.exec_(self.mapToGlobal(pos))

    def __line_widget_line_count_changed(self):
        if self.lineWidget:
            n = int(self.document().lineCount())
            self.lineWidget.changeLineCount(n)
    def canInsertFromMimeData(self, source):
        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)

    def _insert_img(self, u, document, cursor):
        image = QtGui.QImage(u.toLocalFile())
        document.addResource(QtGui.QTextDocument.ImageResource, u, image)
        cursor.insertImage(u.toLocalFile())

    @property
    def _image_folder(self):
        path = os.path.join('qt_app', 'images')
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        document = self.document()

        if source.hasImage():
            image = source.imageData()
            img_path = os.path.join(self._image_folder, f'{uuid.uuid4()}.jpg')
            image.save(os.path.join(img_path))
            u = QtGui.QUrl('file:///' + os.path.join(os.getcwd(), img_path))
            self._insert_img(u, document, cursor)
            return
        elif source.hasUrls():
            for u in source.urls():
                file_ext = os.path.splitext(str(u.toLocalFile()))[1].lower()
                if u.isLocalFile() and file_ext in ['.jpg','.png','.bmp']:
                    self._insert_img(u, document, cursor)
                else:
                    break
            else:
                return

        super(TextEdit, self).insertFromMimeData(source)

class TabBar(QtWidgets.QTabBar):
    def __init__(self):
        super().__init__()

    def enterEvent(self, event):
        index = self.tabAt(event.pos())
        if index != -1:
            self.updateCloseButtonIcon(index, hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        index = self.tabAt(event.pos())
        if index != -1:
            self.updateCloseButtonIcon(index, hover=False)
        super().leaveEvent(event)

    def updateCloseButtonIcon(self, index, hover):
        close_button = self.tabButton(index, QtWidgets.QTabBar.RightSide)
        if close_button:
            if hover:
                close_button.setIcon(QtGui.QIcon('ui/res/x-square-fill-hover.svg'))
            else:
                close_button.setIcon(QtGui.QIcon('ui/res/x-square-fill.svg'))

class TabWidget (QtWidgets.QTabWidget):
    def __init__ (self, MainWindow=None, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.MainWindow = MainWindow
        self.moveRange = None
        self.setMovable(True)

    def setMovable(self, movable):
        if movable == self.isMovable():
            return
        QtWidgets.QTabWidget.setMovable(self, movable)
        if movable:
            self.tabBar().installEventFilter(self)
        else:
            self.tabBar().removeEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.tabBar():
            if event.type() == QtCore.QEvent.MouseButtonPress and event.buttons() == QtCore.Qt.LeftButton:
                QtCore.QTimer.singleShot(0, self.setMoveRange)
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                self.moveRange = None
            elif event.type() == QtCore.QEvent.MouseMove and self.moveRange is not None:
                if event.x() < self.moveRange[0] or event.x() > self.tabBar().width() - self.moveRange[1]:
                    return True
        return QtWidgets.QTabWidget.eventFilter(self, source, event)

    def setMoveRange(self):
        tabRect = self.tabBar().tabRect(self.currentIndex())
        pos = self.tabBar().mapFromGlobal(QtGui.QCursor.pos())
        self.moveRange = pos.x() - tabRect.left(), tabRect.right() - pos.x()

    def closeTab(self, currentIndex):
        self.setCurrentIndex(currentIndex)
        tab = self.currentWidget()
        if tab.file:
            self.MainWindow.recentFiles.append(tab.file)
        if not (tab.saved and tab.canSave):
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle("VarTexter2 - Exiting")
            dlg.setText("File is unsaved. Do you want to close it?")
            dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

            yesButton = dlg.button(QtWidgets.QMessageBox.Yes)
            noButton = dlg.button(QtWidgets.QMessageBox.No)
            cancelButton = dlg.button(QtWidgets.QMessageBox.Cancel)

            yesButton.setStyleSheet("QPushButton { color: white;}")
            noButton.setStyleSheet("QPushButton { color: white;}")
            cancelButton.setStyleSheet("QPushButton { color: white;}")
            dlg.setDefaultButton(cancelButton)
            
            dlg.setStyleSheet("QtWidgets.QMessageBox { background-color: black; } QLabel { color: white; }")
            
            result = dlg.exec_()

            if result == QtWidgets.QMessageBox.Yes:
                self.MainWindow.saveFile(tab.file)
            elif result == QtWidgets.QMessageBox.No:
                print("No")
                tab.deleteLater()
                self.removeTab(currentIndex)
            elif result == QtWidgets.QMessageBox.Cancel:
                print("Cancel selected")
        else:
            tab.deleteLater()
            self.removeTab(currentIndex)

class FileReadThread(QtCore.QThread):
    chunkRead = pyqtSignal(str)
    finishedReading = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, file_path, tab, parent=None):
        super(FileReadThread, self).__init__(parent)
        self.file_path = file_path
        self.tab = tab
        self._is_running = True
        self.parent = parent

    def run(self):
        filep = open(self.file_path, 'rb')
        m = chardet.detect(filep.read(1024*3))
        fencoding = m["encoding"]
        print(fencoding)
        filep.close()
        if fencoding:
            file = open(self.file_path, 'r', encoding=fencoding)
            self.tab.encoding = fencoding.upper()
            while self._is_running:
                chunk = file.read(1024*400)
                if not chunk:
                    break
                self.chunkRead.emit(str(chunk))
                self.msleep(3)
            file.close()
            self.finishedReading.emit()
        else:
            file = open(self.file_path, 'rb', encoding=fencoding)
            self.tab.encoding = "BYTES"
            while self._is_running:
                chunk = file.read(1024*400)
                if not chunk:
                    break
                self.chunkRead.emit(str(chunk))
                self.msleep(3)
            file.close()
            self.finishedReading.emit()
        self.finished.emit()
    def stop(self):
        self._is_running = False
        self.tab.saved = True
        print("SAVED")

class FileWriteThread(QtCore.QThread):
    finishedReading = pyqtSignal()

    def __init__(self, tab, text, parent=None):
        super(FileWriteThread, self).__init__(parent)
        self.tab = tab
        self.text = text
        self._is_running = True
        self.parent = parent

    def run(self):
        with open(self.tab.file, "a+", encoding=self.tab.encoding or "utf-8") as f:
            f.truncate(0)
            f.write(self.text)
            f.close()
            self.tab.saved = True
        self.finishedReading.emit()
        self._is_running = False

    def stop(self):
        self._is_running = False

class LoadingOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignCenter)

        self.label = QtWidgets.QLabel("Loading, please wait...")
        self.layout.addWidget(self.label)

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setRange(0, 0)
        self.layout.addWidget(self.progressBar)

class StaticInfo:
    @staticmethod
    def get_platform():
        current_platform = platform.system()
        if current_platform == "Darwin":
            return "OSX"
        return current_platform
    
    @staticmethod
    def get_basedir():
        return os.path.dirname(os.path.abspath(__file__))
    
    @staticmethod
    def get_filedir(filepath):
        return os.path.dirname(os.path.abspath(filepath))

    @staticmethod
    def replace_consts(data, constants):
        if isinstance(data, dict):
            return {key: StaticInfo.replace_consts(value, constants) for key, value in data.items()}
        elif isinstance(data, list):
            return [StaticInfo.replace_consts(item, constants) for item in data]
        elif isinstance(data, str):
            try:
                return data.format(**constants)
            except KeyError as e:
                print(f"Missing key in constants: {e}")
                return data
            except ValueError:
                return data.replace('{', '{{').replace('}', '}}')
        return data

import sys, importlib, json, configparser
from PyQt5 import QtCore, QtGui, QtWidgets
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
        text = shortcut_info.get("text", "Action")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = QtWidgets.QAction(self)
        action.setText(text)
        action.setShortcut(key_sequence)
        self.registerCommand(command)
        action.triggered.connect(lambda: self.execute_command(command))
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
                if args:
                    out = c.get("command")(args)
                else:
                    out = c.get("command")()
                if out:
                    self.log += f"\nCommand '{command}' returned '{out}'"
            except Exception as e:
                self.log += f"\nFound error in '{command}' - '{e}'.\nInfo: {c}"
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
                        self.log += f"\nFound error in '{main_module}' - {e}"
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