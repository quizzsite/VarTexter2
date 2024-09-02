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
        self.setFontPointSize(3)
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

        self.minimap = MiniMap(self)
        self.minimap.setTextEdit(self)

        self.layout = QtWidgets.QHBoxLayout()
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
    def __init__(self, tabwidget):
        super().__init__()
        self.tabWidget = tabwidget
        self.savedStates = []
        self.setMovable(True)
        self.setTabsClosable(True)
    
    def setTabSaved(self, tab, saved):
        if not tab in [i.get("tab") for i in self.savedStates]:
            self.savedStates.append({"tab": tab, "saved": saved})
        else:
            next((i for i in self.savedStates if i.get("tab") == tab), {})["saved"] = saved
        self.updateTabStyle(next((i for i in self.savedStates if i.get("tab") == tab), {}))

    def updateTabStyle(self, info):
        if info.get("tab"):
            idx = self.tabWidget.indexOf(info.get('tab'))
            if idx != -1:
                if info.get("saved"):
                    self.setStyleSheet(f"QTabBar::tab:selected {{ border-bottom: 2px solid white; }} QTabBar::tab:nth-child({idx+1}) {{ background-color: white; }}")
                else:
                    self.setStyleSheet(f"QTabBar::tab:selected {{ border-bottom: 2px solid yellow; }} QTabBar::tab:nth-child({idx+1}) {{ background-color: yellow; }}")

class TabWidget (QtWidgets.QTabWidget):
    def __init__ (self, MainWindow=None, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.MainWindow = MainWindow
        self.moveRange = None
        self.setMovable(True)
        self.tabbar = TabBar(self)
        self.setTabBar(self.tabbar)
        self.currentChanged.connect(self.onCurrentChanged)

    def onCurrentChanged(self, index):
        current_tab = self.currentWidget()
        self.tabbar.updateTabStyle({"tab": current_tab, "saved": self.isSaved(current_tab)})

    def isSaved(self, tab):
        return any(i.get("tab") == tab and i.get("saved") for i in self.tabbar.savedStates)

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
        if not self.isSaved(tab):
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle("VarTexter2 - Exiting")
            dlg.setText("File is unsaved. Do you want to save it?")
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
                self.MainWindow.api.execute_command(f"saveFile {tab.file}")
                tab.deleteLater()
                self.removeTab(currentIndex)
                self.MainWindow.api.tabClosed.emit(currentIndex, tab.file)
            elif result == QtWidgets.QMessageBox.No:
                tab.deleteLater()
                self.removeTab(currentIndex)
                self.MainWindow.api.tabClosed.emit(currentIndex, tab.file)
            elif result == QtWidgets.QMessageBox.Cancel:
                pass
        else:
            tab.deleteLater()
            self.removeTab(currentIndex)
            self.MainWindow.api.tabClosed.emit(currentIndex, tab.file)

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
    
