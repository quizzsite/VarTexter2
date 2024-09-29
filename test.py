from PyQt6.QtWidgets import QCompleter, QPlainTextEdit, QApplication, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6 import QtCore
from PyQt6.QtGui import QTextCursor, QColor, QFont, QSyntaxHighlighter, QTextCharFormat
import re

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Форматы для различных типов текста
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("darkCyan"))

        class_format = QTextCharFormat()
        class_format.setForeground(QColor("darkMagenta"))
        class_format.setFontWeight(QFont.Weight.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGray"))
        comment_format.setFontItalic(True)

        # Регулярные выражения для подсветки
        keywords = [
            r'\bdef\b', r'\bclass\b', r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bwhile\b', r'\bfor\b', r'\bin\b', r'\breturn\b', r'\bimport\b',
            r'\bfrom\b', r'\bas\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b',
            r'\bwith\b', r'\blambda\b', r'\bassert\b', r'\bdel\b'
        ]
        self.highlighting_rules += [(re.compile(pattern), keyword_format) for pattern in keywords]

        # Функции и классы
        self.highlighting_rules.append((re.compile(r'\b[A-Za-z_]\w*(?=\()'), function_format))  # Функции
        self.highlighting_rules.append((re.compile(r'\bclass\s+\w+'), class_format))  # Классы

        # Строки и комментарии
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))  # Двойные кавычки
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))  # Одинарные кавычки
        self.highlighting_rules.append((re.compile(r'#.*'), comment_format))  # Комментарии

    def highlightBlock(self, text):
        # Применение правил подсветки
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class MyCompleter(QCompleter):
    insertText = QtCore.pyqtSignal(str)

    def __init__(self, parent: QPlainTextEdit):
        QCompleter.__init__(self, parent.toPlainText().split(), parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.highlighted.connect(self.setHighlighted)

    def setHighlighted(self, text):
        self.lastSelected = text

    def getSelected(self):
        return self.lastSelected

    def updateModel(self, text: str):
        # Обновление модели на основе текста
        words = list(set(text.split()))
        self.model().setStringList(words)

class AwesomeTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super(AwesomeTextEdit, self).__init__(parent)

        self.completer = MyCompleter(self)
        self.completer.setWidget(self)
        self.completer.insertText.connect(self.insertCompletion)

        self.hiL = PythonHighlighter(self.document())

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
        QPlainTextEdit.focusInEvent(self, event)

    def keyPressEvent(self, event):
        tc = self.textCursor()
        if event.key() in {Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down, 
                           Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt}:
            QPlainTextEdit.keyPressEvent(self, event)
            return
        

        if event.key() == Qt.Key.Key_Tab and self.completer.popup().isVisible():
            self.completer.insertText.emit(self.completer.getSelected())
            self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            return

        QPlainTextEdit.keyPressEvent(self, event)

        self.completer.updateModel(self.toPlainText())

        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        cr = self.cursorRect()

        if len(tc.selectedText()) > 0:
            self.completer.setCompletionPrefix(tc.selectedText())
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0,0))

            cr.setWidth(self.completer.popup().sizeHintForColumn(0) 
            + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editor = AwesomeTextEdit()
        self.setCentralWidget(self.editor)

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
