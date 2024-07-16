import sys, uuid, json, traceback
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from datetime import datetime
from plugs import *
from ctypes import byref, c_bool, sizeof, windll
from ctypes.wintypes import BOOL, MSG
from winreg import QueryValueEx, ConnectRegistry, HKEY_CURRENT_USER, OpenKey, KEY_READ
from enum import Enum
import charset_normalizer as chardet

class DWMWINDOWATTRIBUTE(Enum):
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20

class LineNumberWidget(QtWidgets.QTextBrowser):
    def __init__(self, widget):
        super().__init__()
        self.__initUi(widget)

    def __initUi(self, widget):
        self.__lineCount = widget.document().lineCount()
        self.__size = int(widget.font().pointSizeF())
        self.__styleInit()

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        self.verticalScrollBar().setEnabled(False)

        widget.verticalScrollBar().valueChanged.connect(self.__changeLineWidgetScrollAsTargetedWidgetScrollChanged)

        self.__initLineCount()

    def __changeLineWidgetScrollAsTargetedWidgetScrollChanged(self, v):
        self.verticalScrollBar().setValue(v)

    def __initLineCount(self):
        for n in range(1, self.__lineCount+1):
            self.append(str(n))

    def changeLineCount(self, n):
        max_one = max(self.__lineCount, n)
        diff = n-self.__lineCount
        if max_one == self.__lineCount:
            first_v = self.verticalScrollBar().value()
            for i in range(self.__lineCount, self.__lineCount + diff, -1):
                self.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
                self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.MoveAnchor)
                self.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
                self.textCursor().removeSelectedText()
                self.textCursor().deletePreviousChar()
            last_v = self.verticalScrollBar().value()
            if abs(first_v-last_v) != 2:
                self.verticalScrollBar().setValue(first_v)
        else:
            for i in range(self.__lineCount, self.__lineCount + diff, 1):
                self.append(str(i + 1))
            self.moveCursor(QtGui.QTextCursor.Start, QtGui.QTextCursor.MoveAnchor)
            

        self.__lineCount = n

    def setValue(self, v):
        self.verticalScrollBar().setValue(v)

    def setFontSize(self, s: float):
        self.__size = int(s)
        self.__styleInit()

    def __styleInit(self):
        self.__style = f'''
                       QTextBrowser 
                       {{ 
                       background: transparent; 
                       border: none; 
                       color: #AAA; 
                       font: {self.__size}pt;
                       }}
                       '''
        self.setStyleSheet(self.__style)
        self.setFixedWidth(self.__size*5)

class MiniMap(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setFixedWidth(150)
        self.setTextInteractionFlags (QtCore.Qt.NoTextInteraction) 
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
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
    def __init__(self, parent):
        super().__init__()
        self.textChanged.connect(self.__line_widget_line_count_changed)
        self.lineWidget = LineNumberWidget(self)

        self.minimap = MiniMap(self)
        self.minimap.setTextEdit(self)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.lineWidget)
        self.layout.addWidget(self)

        self.minimap_scroll_area = QtWidgets.QScrollArea()
        self.minimap_scroll_area.setWidget(self.minimap)
        self.minimap_scroll_area.setFixedWidth(150)
        self.minimap_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.minimap_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.layout.addWidget(self.minimap_scroll_area)

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

class TabWidget (QtWidgets.QTabWidget):
    def __init__ (self, MainWindow=None, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.MainWindow = MainWindow

    def closeTab(self, currentIndex):
        self.setCurrentIndex(currentIndex)
        tab = self.currentWidget()
        print(tab.file)
        if tab.file:
            self.MainWindow.recentFiles.append(tab.file)
        if not tab.saved or tab.canSave:
            dlg = QtWidgets.QDialog()
            dlg.setWindowTitle("VarTexter2 - Exiting")
            saveLabel = QtWidgets.QLabel(dlg)
            saveLabel.setText("File is unsaved. Do you want to close it?")
            QBtn = QtWidgets.QDialogButtonBox.Yes | QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Cancel
            self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
            excD = dlg.exec()
            if excD:
                MainWindow.saveFile(tab.file)
            elif excD == None:
                pass
            if excD == False:
                tab.deleteLater()
                self.removeTab(currentIndex)

class FileReadThread(QtCore.QThread):
    chunkRead = pyqtSignal(str)
    finishedReading = pyqtSignal()

    def __init__(self, file_path, tab, parent=None):
        super(FileReadThread, self).__init__(parent)
        self.file_path = file_path
        self.tab = tab
        self._is_running = True

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
        
        self.tab.textEdit.setText(text)
        self.tab.textEdit.setObjectName("textEdit")

        self.verticalLayout.addLayout(self.tab.textEdit.layout)

        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), name or "Untitled")
        self.tabWidget.currentChanged.connect(self.tabChanged)
        return self.tab

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

    # def openFile(self, f=None, ft="normal", encoding="utf-8"):
    #     files = f or self.openFileDialog()[0]
    #     for f in files:
    #         if ft == "normal":
    #             try:
    #                 file = open(f, 'rb')
    #                 m = chardet.detect(file.read())
    #                 fencoding = m["encoding"]
    #                 file.close()
    #                 file = open(f, "r", encoding=fencoding or encoding)
    #                 editable = True
    #                 tab = self.addTab(name=os.path.basename(f), text=str(file.read()), editable=editable)
    #                 tab.file = f
    #                 tab.encoding = fencoding.upper() or encoding.upper()
    #                 self.tabWidget.setCurrentIndex(-1)
    #                 file.close()
    #             except:
    #                 self.openFile([f], ft="bytes")
    #         elif ft == "bytes":
    #             file = open(f, "rb")
    #             editable = False
    #             tab = self.addTab(name=os.path.basename(f), text=str(file.read()), editable=editable)
    #             tab.file = f
    #             tab.encoding = "BYTES"
    #             tab.canSave = False
    #             self.tabWidget.setCurrentIndex(-1)
    #             file.close()
    def openFile(self, filePath=None, encoding=None):
        if not filePath:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Open File", "", "All Files (*);;Text Files (*.txt)")
            if not filePath:
                return
        for file in filePath:
            encoding = encoding or 'utf-8'
            tab = self.addTab(name=file, editable=True)

            self.loadingOverlay.setGeometry(self.centralWidget().rect())
            self.loadingOverlay.show()

            self.thread = FileReadThread(file, tab)
            self.thread.chunkRead.connect(tab.textEdit.append)
            self.thread.finishedReading.connect(self.loadingOverlay.hide)
            self.thread.finishedReading.connect(lambda: self.encodingLabel.setText(encoding))
            self.thread.start()

    def saveFile(self):
        pass

    def windowInitialize(self):
        tabLog = json.load(open("tablog.json", "r+"))
        for tab in tabLog:
            tab = tabLog.get(tab)
            tabc = self.addTab(name=tab.get("name"), text=tab.get("text"))
            tabc.file = tab.get("file") or None
            tabc.canSave = tab.get("canSave")

    def closeEvent(self, e=False):
        recLog = open("recent.f", "w+")
        recLog.truncate(0)
        recLog.write(str(self.recentFiles))
        recLog.close()

        tabLog = open("tablog.json", "a+")
        tabLog.truncate(0)
        tabs = {}
        for idx in reversed(range(self.tabWidget.count())):
            widget = self.tabWidget.widget(idx)
            if widget and isinstance(widget, QtWidgets.QWidget):
                tabs[str(idx)] = {
                    "name": self.tabWidget.tabText(idx),
                    "file": getattr(widget, 'file', None),
                    "canSave": getattr(widget, 'canSave', None),
                    "text": widget.textEdit.toHtml(),
                    "modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        json.dump({str(idx): tabs[str(idx)] for idx in range(len(tabs))}, tabLog)
        e.accept()

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        dwmapi = windll.LoadLibrary("dwmapi")
        self.__dwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        self.__detect_theme_flag = True
        self.__initTheme()

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
