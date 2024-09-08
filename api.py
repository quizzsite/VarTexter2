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
                    self.__window.logger.log += f"\nFound new plugin with info {plugInfo}"
                    self.__window.api.regAll(plugin)
        finally:
            sys.path.pop(0)
            self.__window.api.commandsLoaded.emit()

    def load_plugin(self, pluginDir):
        sys.path.insert(0, pluginDir)
        if os.path.isdir(os.path.join(self.plugin_directory, pluginDir)) and os.path.isfile(f"{os.path.join(self.plugin_directory, pluginDir)}\config.ini"):
            plugInfo = self.__window.api.load_ini_file(f"{os.path.join(self.plugin_directory, pluginDir)}\config.ini")
            self.plugins.append(plugInfo)
            self.__window.logger.log += f"\nFound new plugin with info {plugInfo}"
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
    treeWidgetDoubleClicked = pyqtSignal(QModelIndex)
    treeWidgetActivated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.__window = parent
        self.__version__ = self.__window.__version__
        self.menu_map = {}
        self.commands = {}
        self.setTreeWidgetModel("/")

        self.__window.treeView.doubleClicked.connect(self.onDoubleClicked)
        self.__window.treeView.clicked.connect(self.onClicked)
        self.__window.treeView.activated.connect(self.onActivated)
        # self.__window.treeView.customContextMenuRequested.connect()

    def __str__(self):
        return f"""\n------------------------------VtAPI--version--{str(self.__version__)}------------------------------\nDocumentation:https://wtfidklol.com"""

    def onDoubleClicked(self, index):        self.treeWidgetDoubleClicked.emit(index)

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
                menu = self.menu_map.setdefault(menu_id, QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window))
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
                            action.triggered.connect(lambda checked, cmd=item['command']: self.executeCommand(cmd))
                        parent.addAction(action)
                        if 'shortcut' in item:
                            action.setShortcut(QtGui.QKeySequence(item['shortcut']))
    def findMenu(self, menu, n):
        if menu:
            if menu.get("id") == n:
                return menu
            for c in menu.get("children", []):
                found = self.findMenu(c, n)
                if found:
                    return found
        return None

    def loadThemes(self):
        if os.path.isdir(self.__window.themesDir):
            with open(self.__window.mb, "r+") as file:
                menus = json.load(file)
                file.close()
            themeMenu = None
            for menu in menus:
                themeMenu = self.findMenu(menu, "themes")
            if themeMenu:
                themeMenu["children"].clear()
                for theme in os.listdir(self.__window.themesDir):
                    if os.path.isfile(os.path.join(self.__window.themesDir, theme)):
                        themeMenu["children"].append({"caption": theme, "command": f"setTheme {theme}"})
                json.dump(menus, open(self.__window.mb, "w+"))

    def executeCommand(self, command):
        commandnargs = command.split()
        c = self.commands.get(commandnargs[0])
        if c:
            try:
                args = commandnargs[1:]
                if args:
                    out = c.get("command")(args)
                    self.__window.logger.log += f"\nExecuted command '{command}' with args '{args}'"
                else:
                    out = c.get("command")()
                    self.__window.logger.log += f"\nExecuted command '{command}'"
                if out:
                    self.__window.logger.log += f"\nCommand '{command}' returned '{out}'"
            except Exception as e:
                print(e)
                self.__window.logger.log += f"\nFound error in '{command}' - '{e}'.\nInfo: {c}"
        else:
            self.__window.logger.log += f"\nCommand '{command}' not found"

    def initAPI(self, plugin):
        sys.path.insert(0, os.path.dirname(plugin.get("path")))
        main_module = plugin.get("main")
        if main_module.endswith('.py'):
            main_module = main_module[:-3]
            plug = self.importModule(
                str(os.path.join(os.path.dirname(plugin.get("path")), plugin.get("main"))),
                plugin.get("name") + "Plugin"
            )
            if hasattr(plug, "initAPI"):
                plug.initAPI(self)
            return plug

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
                self.commands[commandN] = self.command
            except (ImportError, AttributeError) as e:
                self.__window.logger.log += f"\nError when registering '{commandN}' from '{pl}': {e}"
        else:
            self.command = {}
            command_func = getattr(self.__window, commandN, None)
            if command_func:
                self.command["command"] = command_func
                self.command["plugin"] = None
                self.commands[commandN] = self.command
            else:
                self.__window.logger.log += f"\nCommand '{commandN}' not found"

    def removeCommand(self, command_name):
        if command_name in self.commands:
            del self.commands[command_name]
            self.__window.logger.log += f"\nUnregistered command '{command_name}'"

    def removeMenu(self, menu_id):
        if menu_id in self.menu_map:
            menu = self.menu_map.pop(menu_id)
            menu.deleteLater()
            self.__window.logger.log += f"\nRemoved menu with ID '{menu_id}'"

    def removeShortcut(self, shortcut_info):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = next((a for a in self.__window.actions() if a.shortcut() == key_sequence), None)
        
        if action:
            self.__window.removeAction(action)
            self.__window.logger.log += f"\nRemoved shortcut '{command}'"

    def getCommands(self):
        return self.commands

    def getCommand(self, name):
        return self.commands.get(name)

    def textChangeEvent(self, i):
        tab = self.__window.tabWidget.widget(i)
        tab.textEdit.textChanged.connect(self.textChngd)

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
        self.__window.setWindowTitle(f"{self.__window.tabWidget.tabText(index)} - VarTexter2")
        if index >= 0: self.__window.encodingLabel.setText(self.__window.tabWidget.widget(index).encoding)
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