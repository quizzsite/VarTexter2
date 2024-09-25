from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import pyqtSignal, QObject, QModelIndex
import sys
import os
import json
import importlib
import configparser

class PluginManager:
    def __init__(self, plugin_directory: str, w):
        self.plugin_directory = plugin_directory
        self.__window = w
        self.plugins = []
    
    def load_plugins(self): self._load_plugins()

    def _load_plugins(self):
        try:
            sys.path.insert(0, self.plugin_directory)
            for plugDir in os.listdir(self.plugin_directory):
                if os.path.isdir(os.path.join(self.plugin_directory, plugDir)) and os.path.isfile(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini"):
                    plugInfo = self.__window.api.load_ini_file(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini")
                    plugin = self.__window.api.initAPI(plugInfo)
                    # if int(self.__window.api.__version__) == int(self.__window.appVersion):
                    self.plugins.append(plugInfo)
                    self.__window.api.setLogMsg(f"\nFound new plugin with info {plugInfo}")
                    self.__window.api.regAll(plugin)
        finally:
            sys.path.pop(0)
            self.__window.api.commandsLoaded.emit()

    def load_plugin(self, pluginDir):
        sys.path.insert(0, pluginDir)
        if os.path.isdir(os.path.join(self.plugin_directory, pluginDir)) and os.path.isfile(f"{os.path.join(self.plugin_directory, pluginDir)}\config.ini"):
            plugInfo = self.__window.api.load_ini_file(rf"{os.path.join(self.plugin_directory, pluginDir)}\config.ini")
            self.plugins.append(plugInfo)
            self.setLogMsg(f"\nFound new plugin with info {plugInfo}")
            self.__window.api.regAll()
            self.__window.api.initAPI(plugInfo)
            sys.path.pop(0)

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

    def load_ini_file(self, ini_path):
        plugin = ini_path
        config = configparser.ConfigParser()
        config.read(plugin)

        self.name = config.get('DEFAULT', 'name', fallback='Unknown Plugin')

        self.version = config.get('DEFAULT', 'version', fallback='1.0')

        self.main_script = config.get('DEFAULT', 'main', fallback='')

        self.plugInfo = {"name": self.name, "version": self.version, "path": ini_path, "main": self.main_script}

        self.cm = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'cm', fallback=''))) if config.get('DEFAULT', 'cm', fallback='') else ""

        self.tcm = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'tcm', fallback=''))) if config.get('DEFAULT', 'tcm', fallback='') else ""
    
        self.mb = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'mb', fallback=''))) if config.get('DEFAULT', 'mb', fallback='') else ""
    
        self.sc = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'sc', fallback=''))) if config.get('DEFAULT', 'sc', fallback='') else ""
    
        return self.plugInfo

    def regAll(self, plugin):
        if self.mb:
            self.parseMenu(json.load(open(self.mb, "r+")), self.__window.menuBar(), pl=plugin)
            self.plugInfo["mb"] = self.mb

        if self.cm:
            self.parseMenu(json.load(open(self.cm, "r+")), self.__window.contextMenu, pl=plugin)
            self.plugInfo["cm"] = self.cm

        if self.tcm:
            self.parseMenu(json.load(open(self.tcm, "r+")), self.__window.textContextMenu, pl=plugin)
            self.plugInfo["tcm"] = self.tcm

        if self.sc:
            for shortcut in json.load(open(self.sc, "r+")):
                self.createShortcut(shortcut, pl=plugin)            
            self.plugInfo["sc"] = self.sc

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

    def parseMenu(self, data, parent, pl=None):
        if isinstance(data, dict):
            data = [data]

        for item in data:
            menu_id = item.get('id')
            if menu_id:
                menu = self.__menu_map.setdefault(menu_id, QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window))
                menu.setObjectName(menu_id)
                fmenu = self.findMenu(self.__menu_map, menu_id)
                if not fmenu:
                    parent.addMenu(menu)
                if 'children' in item:
                    self.parseMenu(item['children'], menu, pl)
            else:
                if 'children' in item:
                    submenu = QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window)
                    self.parseMenu(item['children'], submenu)
                    parent.addMenu(submenu)
                else:
                    if item.get('caption') == "-":
                        parent.addSeparator()
                    else:
                        action = QtGui.QAction(item.get('caption', 'Unnamed'), self.__window)
                        if 'command' in item:
                            self.registerCommand(item['command'], pl)
                            args = item.get("args")
                            kwargs = item.get("kwargs")
                            action.triggered.connect(lambda checked, cmd=item['command'], args=args or [], kwargs=kwargs or {}: 
                                self.executeCommand(
                                    cmd, 
                                    *args, 
                                    **({**kwargs, 'checked': checked} if action.isCheckable() else kwargs)
                                )
                            )
                            parent.addAction(action)
                        if 'shortcut' in item:
                            action.setShortcut(QtGui.QKeySequence(item['shortcut']))
                        if 'checkable' in item:
                            action.setCheckable(item['checkable'])

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
                found_menu = self.findMenuInQMenu(menu, menu_id)
                if found_menu:
                    return found_menu
        return None

    def findMenuInQMenu(self, menu, menu_id):
        for action in menu.actions():
            submenu = action.menu()
            if submenu:
                if submenu.objectName() == menu_id:
                    return submenu
                found_menu = self.findMenuInQMenu(submenu, menu_id)
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

    def executeCommand(self, command, *args, **kwargs):
        c = self.__commands.get(command)
        if c:
            try:
                out = c.get("command")(*args, **kwargs)
                self.setLogMsg(f"\nExecuted command '{command}' with args '{args}', kwargs '{kwargs}'")
                if out:
                    self.setLogMsg(f"\nCommand '{command}' returned '{out}'")
            except Exception as e:
                print(e)
                self.setLogMsg(f"\nFound error in '{command}' - '{e}'.\nInfo: {c}")
        else:
            self.setLogMsg(f"\nCommand '{command}' not found")

    def initAPI(self, plugin):
        sys.path.insert(0, os.path.dirname(plugin.get("path")))
        main_module = plugin.get("main")
        if main_module.endswith('.py'):
            main_module = main_module[:-3]
            try:
                plug = self.importModule(
                str(os.path.join(os.path.dirname(plugin.get("path")), plugin.get("main"))),
                plugin.get("name") + "Plugin"
                )
                if hasattr(plug, "initAPI"):
                    plug.initAPI(self)
                return plug
            except Exception as e:
                self.setLogMsg(f"\nFailed to import module '{plugin.get('path')}': '{e}'")

    def importModule(self, path, n):
        spec = importlib.util.spec_from_file_location(n, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[n] = module
        spec.loader.exec_module(module)
        return module

    def registerCommand(self, command, pl=None):
        commandN = command.split()[0]
        if pl:
            try:
                command_func = getattr(pl, commandN)
                self.command = {}
                self.command["command"] = command_func
                self.command["plugin"] = pl
                self.__commands[commandN] = self.command
            except (ImportError, AttributeError) as e:
                self.setLogMsg(f"\nError when registering '{commandN}' from '{pl}': {e}")
        else:
            self.command = {}
            command_func = getattr(self.__window, commandN, None)
            if command_func:
                self.command["command"] = command_func
                self.command["plugin"] = None
                self.__commands[commandN] = self.command
            else:
                self.setLogMsg(f"\nCommand '{commandN}' not found")

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