import uuid, platform, os, re
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import pyqtSlot

from PyQt6.QtWidgets import QTextEdit, QCompleter
from PyQt6.QtCore import QStringListModel, Qt
from PyQt6.QtGui import QTextCursor, QKeyEvent

class ConsoleWidget(QtWidgets.QDockWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setWindowTitle(self.window.appName+" - Console")
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
        self.consoleWidget = QtWidgets.QWidget()
        self.consoleWidget.setObjectName("consoleWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.consoleWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(parent=self.consoleWidget)
        self.textEdit.setReadOnly(True)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self.textEdit.setObjectName("consoleOutput")
        self.verticalLayout.addWidget(self.textEdit)
        self.lineEdit = QtWidgets.QLineEdit(parent=self.consoleWidget)
        self.lineEdit.setMouseTracking(False)
        self.lineEdit.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.lineEdit.setCursorMoveStyle(QtCore.Qt.CursorMoveStyle.LogicalMoveStyle)
        self.lineEdit.setObjectName("consoleCommandLine")
        self.verticalLayout.addWidget(self.lineEdit)
        self.setWidget(self.consoleWidget)
        self.lineEdit.returnPressed.connect(self.sendCommand)
    def sendCommand(self):
        text = self.lineEdit.text()
        if text:
            if text.startswith("vtapi"):
                if len(text.split(".")) == 2:
                    apiCommand = text.split(".")[-1] 
                    if hasattr(self.window.api, apiCommand):
                        self.window.logger.log += str(getattr(self.window.api, apiCommand)())
                self.window.logger.log += str(self.window.api)
                self.lineEdit.clear()
            else:
                self.window.pl.executeCommand({"command": self.lineEdit.text()})
                self.lineEdit.clear()
    def closeEvent(self, e):
        self.window.pl.executeCommand({"command": "logConsole"})
        e.ignore()

class MiniMap(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setFixedWidth(150)
        self.setObjectName("miniMap")
        self.setTextInteractionFlags (QtCore.Qt.TextInteractionFlag.NoTextInteraction) 
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self._isDragging = False

    def setTextEdit(self, text_edit):
        self.textEdit = text_edit
        self.setHtml(self.textEdit.toHtml())
        self.textEdit.verticalScrollBar().valueChanged.connect(self.syncScroll)
        self.textEdit.cursorPositionChanged.connect(self.syncSelection)
        self.textEdit.verticalScrollBar().rangeChanged.connect(self.update_minimap)
        self.textEdit.textChanged.connect(self.update_minimap)
        self.setFontPointSize(3)
        self.update_minimap()
        self.viewport().update()

    def contextMenu(self):
        menu = QtWidgets.QMenu()
        a = QtGui.QAction("dwkde[wek]", self)
        a.setCheckable(True)
        menu.addAction(a)
        menu.exec(QtGui.QCursor.pos())

    @pyqtSlot()
    def syncScroll(self):
        maxValue = self.textEdit.verticalScrollBar().maximum()
        if maxValue != 0:
            value = self.textEdit.verticalScrollBar().value()
            ratio = value / maxValue
            self.verticalScrollBar().setValue(int(ratio * self.verticalScrollBar().maximum()))
        self.viewport().update()

    def syncSelection(self):
        c = QtGui.QTextCursor(self.textEdit.document())
        c.setPosition(self.textEdit.textCursor().selectionStart())
        c.setPosition(self.textEdit.textCursor().selectionEnd(), QtGui.QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(c)
        self.viewport().update()

    @pyqtSlot()
    def update_minimap(self):
        self.setPlainText(self.textEdit.toPlainText())
        self.syncScroll()
        self.viewport().update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._isDragging = True
            self.syncScroll_from_position(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._isDragging:
            self.syncScroll_from_position(event.pos())
            self.textCursor().clearSelection()
        super().mouseMoveEvent(event)
        self.textCursor().clearSelection()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.textCursor().clearSelection()
            self._isDragging = False
        super().mouseReleaseEvent(event)

    def syncScroll_from_position(self, pos):
        if self.viewport().height() != 0:
            ratio = pos.y() / self.viewport().height()
            value = int(ratio * self.textEdit.verticalScrollBar().maximum())
            self.textEdit.verticalScrollBar().setValue(value)
            self.textCursor().clearSelection()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        scroll_bar = self.textEdit.verticalScrollBar()
        scroll_bar.setValue(int(scroll_bar.value() - delta / 1.5))

    def resizeEvent(self, event):
        self.update_minimap()
        super().resizeEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.textEdit is None:
            return

        viewportRect = self.textEdit.viewport().rect()
        content_rect = self.textEdit.document().documentLayout().blockBoundingRect(self.textEdit.document().firstBlock()).united(
            self.textEdit.document().documentLayout().blockBoundingRect(self.textEdit.document().lastBlock())
        )

        viewportHeight = self.viewport().height()
        contentHeight = content_rect.height()
        if contentHeight == 0:
            return
        scaleFactor = viewportHeight / contentHeight

        visibleRectHeight = viewportRect.height() * scaleFactor
        visibleRectTop = self.textEdit.verticalScrollBar().value() * scaleFactor

        visibleRect = QtCore.QRectF(
            0,
            visibleRectTop,
            self.viewport().width(),
            visibleRectHeight
        )

        painter = QtGui.QPainter(self.viewport())
        painter.setBrush(QtGui.QColor(0, 0, 255, 50))
        painter.setPen(QtGui.QColor(0, 0, 255))
        painter.drawRect(visibleRect)

class StandartHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document: QtGui.QTextDocument):
        super().__init__(document)

class StandartCompleter(QCompleter):
    insertText = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QTextEdit):
        QCompleter.__init__(self, parent.toPlainText().split(), parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.highlighted.connect(self.setHighlighted)

    def setHighlighted(self, text):
        self.lastSelected = text

    def getSelected(self):
        return self.lastSelected

    def updateModel(self, text: str):
        words = list(set(text.split()))
        self.model().setStringList(words)

class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

        self.minimap = MiniMap(self)
        self.minimap.setTextEdit(self)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self)

        self.minimapScrollArea = QtWidgets.QScrollArea()
        self.minimapScrollArea.setWidget(self.minimap)
        self.minimapScrollArea.setFixedWidth(150)
        self.minimapScrollArea.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.minimapScrollArea.customContextMenuRequested.connect(self.minimap.contextMenu)
        self.minimapScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.minimapScrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.layout.addWidget(self.minimapScrollArea)

        self.completer = StandartCompleter(self)
        self.completer.setWidget(self)
        self.completer.insertText.connect(self.insertCompletion)

        self.highLighter = StandartHighlighter(self.document())
        self.highLighter.setDocument(self.document())

    def contextMenu(self, pos):
        self.mw.contextMenu.exec(self.mapToGlobal(pos))

    def canInsertFromMimeData(self, source):
        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)

    def _insert_img(self, u, document, cursor):
        image = QtGui.QImage(u.toLocalFile())
        document.addResource(QtGui.QTextDocument.ResourceType.ImageResource, u, image)
        cursor.insertImage(u.toLocalFile())

    @property
    def _image_folder(self):
        path = os.path.join('cache', 'images')
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
            u = QtCore.QUrl('file:///' + os.path.join(os.getcwd(), img_path))
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

    def insertCompletion(self, completion):
        tc = self.textCursor()
        extra = (len(completion) - len(self.completer.completionPrefix()))
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)
        self.completer.popup().hide()

    def focusInEvent(self, event):
        if self.completer and not self.textCursor().hasSelection():
            self.completer.setWidget(self)
        QtWidgets.QTextEdit.focusInEvent(self, event)

    def keyPressEvent(self, event):
        tc = self.textCursor()

        if event.key() in {
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down, 
            Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt
        } or event.modifiers() in {Qt.KeyboardModifier.ControlModifier, Qt.KeyboardModifier.ShiftModifier}:
            QtWidgets.QTextEdit.keyPressEvent(self, event)
            return

        if event.key() == Qt.Key.Key_Tab and self.completer.popup().isVisible():
            self.completer.insertText.emit(self.completer.getSelected())
            self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            return

        QtWidgets.QTextEdit.keyPressEvent(self, event)

        self.completer.updateModel(self.toPlainText())

        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        cr = self.cursorRect()

        if len(tc.selectedText()) > 0 and event.text().isprintable():
            self.completer.setCompletionPrefix(tc.selectedText())
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))

            cr.setWidth(self.completer.popup().sizeHintForColumn(0) 
                        + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

class TabBar(QtWidgets.QTabBar):
    def __init__(self, tabwidget):
        super().__init__()
        self.tabWidget = tabwidget
        self.savedStates = []
        self.setObjectName("tabBar")
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
        self.setObjectName("tabWidget")
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
            if event.type() == QtCore.QEvent.MouseButtonPress and event.buttons() == QtCore.Qt.MouseButton.LeftButton:
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
            dlg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel)

            yesButton = dlg.button(QtWidgets.QMessageBox.StandardButton.Yes)
            noButton = dlg.button(QtWidgets.QMessageBox.StandardButton.No)
            cancelButton = dlg.button(QtWidgets.QMessageBox.StandardButton.Cancel)

            yesButton.setStyleSheet("QPushButton { color: white;}")
            noButton.setStyleSheet("QPushButton { color: white;}")
            cancelButton.setStyleSheet("QPushButton { color: white;}")
            dlg.setDefaultButton(cancelButton)
            
            dlg.setStyleSheet("QtWidgets.QMessageBox { background-color: black; } QLabel { color: white; }")
            
            result = dlg.exec()

            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self.MainWindow.api.execute_command(f"saveFile {tab.file}")
                tab.deleteLater()
                self.removeTab(currentIndex)
                self.MainWindow.api.SigSlots.tabClosed.emit(currentIndex, tab.file)
            elif result == QtWidgets.QMessageBox.StandardButton.No:
                tab.deleteLater()
                self.removeTab(currentIndex)
                self.MainWindow.api.SigSlots.tabClosed.emit(currentIndex, tab.file)
            elif result == QtWidgets.QMessageBox.StandardButton.Cancel:
                pass
        else:
            tab.deleteLater()
            self.removeTab(currentIndex)
            self.MainWindow.api.SigSlots.tabClosed.emit(currentIndex, tab.file)

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
        stack = [data]
        result = data

        while stack:
            current = stack.pop()
            
            if isinstance(current, dict):
                items = list(current.items())
                for key, value in items:
                    if isinstance(value, (dict, list)):
                        stack.append(value)
                    elif isinstance(value, str):
                        try:
                            current[key] = value.format(**constants)
                        except KeyError as e:
                            print(f"Missing key in constants: {e}")
                        except ValueError:
                            current[key] = value.replace('{', '{{').replace('}', '}}')
                        
            elif isinstance(current, list):
                items = list(current)
                for i, item in enumerate(items):
                    if isinstance(item, (dict, list)):
                        stack.append(item)
                    elif isinstance(item, str):
                        try:
                            current[i] = item.format(**constants)
                        except KeyError as e:
                            print(f"Missing key in constants: {e}")
                        except ValueError:
                            current[i] = item.replace('{', '{{').replace('}', '}}')

        return result
    @staticmethod
    def replacePaths(data):
        def replace_var(match):
            env_var = match.group(1)
            return os.getenv(env_var, f'%{env_var}%')
        return re.sub(r'%([^%]+)%', replace_var, data)