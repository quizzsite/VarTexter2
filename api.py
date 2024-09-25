from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import pyqtSignal, QObject, QModelIndex
import sys
import os
import json
import importlib
import configparser

class VtAPI(QObject):

    # windowStarted = pyqtSignal()
    commandsLoaded = pyqtSignal()
    tabClosed = pyqtSignal(int, str)
    tabChanged = pyqtSignal()
    textChanged = pyqtSignal()
    windowClosed = pyqtSignal()

    treeWidgetClicked = pyqtSignal(QModelIndex)
    treeWidgetDoubleClicked = pyqtSignal(QtGui.QFileSystemModel, QModelIndex)
    treeWidgetActivated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.__window = parent
        self.__version__ = self.__window.__version__
        self.__menu_map = {}
        self.__commands = {}
        self.setTreeWidgetModel("/")

        self.__window.treeView.doubleClicked.connect(self.onDoubleClicked)
        self.__window.treeView.clicked.connect(self.onClicked)
        self.__window.treeView.activated.connect(self.onActivated)
        # self.__window.treeView.customContextMenuRequested.connect()

        self.packageDirs = self.__window.packageDirs
        self.pluginsDir = self.__window.pluginsDir
        self.themesDir = self.__window.themesDir
        self.uiDir = self.__window.uiDir

    def __str__(self):
        return f"""\n------------------------------VtAPI--version--{str(self.__version__)}------------------------------\nDocumentation:https://wtfidklol.com"""

    def onDoubleClicked(self, index):        self.treeWidgetDoubleClicked.emit(self.__window.treeView.model(), index)

    def onClicked(self, index):        self.treeWidgetClicked.emit(index)

    def onActivated(self):        self.treeWidgetActivated.emit()

    def createShortcut(self, shortcut_info, pl=None):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        checkable = shortcut_info.get("checkable")
        text = shortcut_info.get("text", "Action")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = QtGui.QAction(self.__window)
        action.setText(text)
        action.setShortcut(key_sequence)
        self.registerCommand(command, pl=pl)
        action.triggered.connect(lambda: self.executeCommand(command))
        self.__window.addAction(action)

    def findAction(self, parent_menu, caption=None, command=None):
        for action in parent_menu.actions():
            if caption and action.text() == caption:
                return action
            if command and hasattr(action, 'command') and action.command == command:
                return action

        for action in parent_menu.actions():
            if action.menu():
                found_action = self.findAction(action.menu(), caption, command)
                if found_action:
                    return found_action

        return None

    def findMenu(self, menubar, menu_id):
        for action in menubar.actions():
            menu = action.menu()
            if menu:
                if menu.objectName() == menu_id:
                    return menu
                found_menu = self.findMenu2(menu, menu_id)
                if found_menu:
                    return found_menu
        return None

    def findMenu2(self, menu, menu_id):
        for action in menu.actions():
            submenu = action.menu()
            if submenu:
                if submenu.objectName() == menu_id:
                    return submenu
                found_menu = self.findMenu2(submenu, menu_id)
                if found_menu:
                    return found_menu
        return None


    def loadThemes(self, menu):
        if os.path.isdir(self.__window.themesDir) and os.path.isfile(self.__window.mb):
            with open(self.__window.mb, "r+") as file:
                try:
                    menus = json.load(file)
                except Exception as e:
                    self.setLogMsg(f"Error when loading '{self.__window.mb}': {e}")
            themeMenu = self.findMenu(menu, "themes")
            if themeMenu:
                themeMenu["children"].clear()
                for theme in os.listdir(self.__window.themesDir):
                    if os.path.isfile(os.path.join(self.__window.themesDir, theme)) and theme[-1:-3] == "qss":
                        themeMenu["children"].append({"caption": theme, "command": f"setTheme {theme}"})
                json.dump(menus, open(self.__window.mb, "w+"))

    def removeCommand(self, command_name):
        if command_name in self.__commands:
            del self.__commands[command_name]
            self.setLogMsg(f"\nUnregistered command '{command_name}'")

    def removeMenu(self, menu_id):
        if menu_id in self.__menu_map:
            menu = self.__menu_map.pop(menu_id)
            menu.deleteLater()
            self.setLogMsg(f"\nRemoved menu with ID '{menu_id}'")

    def removeShortcut(self, shortcut_info):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = next((a for a in self.__window.actions() if a.shortcut() == key_sequence), None)
        
        if action:
            self.__window.removeAction(action)
            self.setLogMsg(f"\nRemoved shortcut '{command}'")

    def updateEncoding(self):
        e = self.getTabEncoding(self.currentTabIndex())
        self.__window.encodingLabel.setText(e)

    def getCommands(self):
        return self.__commands

    def getCommand(self, name):
        return self.__window.pl.regCommands.get(name)

    def textChangeEvent(self, i):
        tab = self.__window.tabWidget.widget(i)
        tab.textEdit.textChanged.connect(self.textChngd)
        tab.textEdit.document().contentsChanged.connect(self.textChngd)

    def openFileDialog(e=None):
        dlg = QtWidgets.QFileDialog.getOpenFileNames(None, "Open File", "", "All Files (*);;Text Files (*.txt)")
        return dlg

    def saveFileDialog(e=None):
        dlg = QtWidgets.QFileDialog.getSaveFileName()
        return dlg

    def currentTabIndex(self):
        return self.__window.tabWidget.indexOf(self.__window.tabWidget.currentWidget())
    
    def getTabTitle(self, i):
        return self.__window.tabWidget.tabText(i)

    def setTabTitle(self, i, text):
        tab = self.__window.tabWidget.widget(i)
        return self.__window.tabWidget.setTabText(self.__window.tabWidget.indexOf(tab), text)

    def getTabText(self, i):
        tab = self.__window.tabWidget.widget(i)
        text = tab.textEdit.toHtml()
        return text

    def setTabText(self, i, text: str | None):
        tab = self.__window.tabWidget.widget(i)
        tab.textEdit.setText(text)
        return text

    def getTabFile(self, i):
        tab = self.__window.tabWidget.widget(i)
        return tab.file

    def setTabFile(self, i, file):
        tab = self.__window.tabWidget.widget(i)
        tab.file = file
        return tab.file
    
    def getTabCanSave(self, i):
        tab = self.__window.tabWidget.widget(i)
        return tab.canSave

    def setTabCanSave(self, i, b: bool):
        tab = self.__window.tabWidget.widget(i)
        tab.canSave = b
        return b

    def getTabCanEdit(self, i):
        tab = self.__window.tabWidget.widget(i)
        return tab.canEdit

    def setTabCanEdit(self, i, b: bool):
        tab = self.__window.tabWidget.widget(i)
        tab.canEdit = b
        tab.textEdit.setReadOnly(b)
        tab.textEdit.setDisabled(b)
        return b

    def getTabEncoding(self, i):
        tab = self.__window.tabWidget.widget(i)
        return tab.encoding

    def setTabEncoding(self, i, enc):
        tab = self.__window.tabWidget.widget(i)
        tab.encoding = enc
        return enc

    def setTab(self, i):
        if i <= -1:
            self.__window.tabWidget.setCurrentIndex(self.__window.tabWidget.count()-1)
        else:
            self.__window.tabWidget.setCurrentIndex(i-1)
        return i

    def getTabSaved(self, i):
        tab = self.__window.tabWidget.widget(i)
        return self.__window.tabWidget.isSaved(tab)

    def setTabSaved(self, i, b: bool):
        tab = self.__window.tabWidget.widget(i)
        self.__window.tabWidget.tabBar().setTabSaved(tab or self.__window.tabWidget.currentWidget(), b)
        return b
    
    def getTextSelection(self, i):
        tab = self.__window.tabWidget.widget(i)
        return tab.textEdit.textCursor().selectedText()

    def getTextCursor(self, i):
        tab = self.__window.tabWidget.widget(i)
        return tab.textEdit.textCursor()

    def setTextSelection(self, i, s, e):
        tab = self.__window.tabWidget.widget(i)
        cursor = tab.textEdit.textCursor()
        cursor.setPosition(s)
        cursor.setPosition(e, QtGui.QTextCursor.MoveMode.KeepAnchor)
        tab.textEdit.setTextCursor(cursor)

    def addCustomTab(self, tab: QtWidgets.QWidget, title):
        self.__window.tabWidget.addTab(tab, title)

    def fileSystemModel(self):
        return QtGui.QFileSystemModel()
    
    def getTreeModel(self):
        return self.model

    def setTreeWidgetModel(self, dir):
        self.model = QtGui.QFileSystemModel()
        self.model.setRootPath(dir)
        self.__window.treeView.setModel(self.model)
        self.__window.treeView.setRootIndex(self.model.index(dir))
        
        return self.model

    def textChngd(self):
        tab = self.__window.tabWidget.currentWidget()
        if tab:
            self.__window.tabWidget.tabBar().setTabSaved(tab, False)

    def tabChngd(self, index):
        if index > -1:
            self.__window.setWindowTitle(f"{os.path.normpath(self.getTabFile(index) or 'Untitled')} - {self.__window.appName}")
            if index >= 0: self.__window.encodingLabel.setText(self.__window.tabWidget.widget(index).encoding)
            self.updateEncoding()
        else:
            self.__window.setWindowTitle(self.__window.appName)
        self.tabChanged.emit()

    def dirOpenDialog(self, e=None):
        dlg = QtWidgets.QFileDialog.getExistingDirectory(
            self.__window.treeView,
            caption="VarTexter - Get directory",
        )
        return str(dlg)
    def setTheme(self, theme):
        themePath = os.path.join(self.__window.themesDir, theme)
        if os.path.isfile(themePath):
            self.__window.setStyleSheet(open(themePath, "r+").read())
    def getLog(self):
        return self.__window.logger.log
    def setLogMsg(self, msg):
        self.__window.logger.log += f"\n{msg}"
    
    def isFile(self, path):
        return os.path.isfile(path)