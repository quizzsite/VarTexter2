from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject, QModelIndex
import weakref
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
    treeWidgetDoubleClicked = pyqtSignal(QModelIndex)
    treeWidgetActivated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.__window = parent
        self.menu_map = {}
        self.commands = {}
        self.__window.setTreeWidgetModel("/")

        self.__window.treeView.doubleClicked.connect(self.onDoubleClicked)
        self.__window.treeView.clicked.connect(self.onClicked)
        self.__window.treeView.activated.connect(self.onActivated)
        # self.__window.treeView.customContextMenuRequested.connect()

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
        action = QtWidgets.QAction(self.__window)
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
                        action = QtWidgets.QAction(item.get('caption', 'Unnamed'), self.__window)
                        if 'command' in item:
                            self.registerCommand(item['command'], pl)
                            action.triggered.connect(lambda checked, cmd=item['command'], args=item.get('args', {}): self.executeCommand(cmd, args))
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
        if os.path.isdir("ui/style"):
            with open("ui/Main.mb", "r+") as file:
                menus = json.load(file)
                for menu in menus:
                    themeMenu = self.findMenu(menu, "themes")
                    if themeMenu:
                        childrens = themeMenu.get("children", [])
                        themeMenu["children"] = [{"caption": theme, "command": f"settheme {theme}"} for theme in os.listdir("ui/style")]
                        break
            with open("ui/Main.mb", "w+") as file:
                file.write(json.dumps(menus))
                file.close()
    def executeCommand(self, command):
        commandnargs = command.split()
        c = self.commands.get(commandnargs[0])
        if c:
            # try:
            args = commandnargs[1:]
            if args:
                out = c.get("command")(args)
            else:
                out = c.get("command")()
            if out:
                self.__window.log += f"\nCommand '{command}' returned '{out}'"
            # except Exception as e:
                # self.__window.log += f"\nFound error in '{command}' - '{e}'.\nInfo: {c}"

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
            command_func = getattr(pl, commandN)
            self.command = {}
            self.command["command"] = command_func
            self.command["plugin"] = pl
            self.commands[commandN] = self.command

                    # except (ImportError, AttributeError) as e:
                        # self.__window.log += f"\nОшибка при регистрации команды '{commandN}' из модуля '{main_module}': {e}"
                    # finally:
                        # sys.path = [p for p in sys.path if p != plugin_dir]
        else:
            self.command = {}
            command_func = getattr(self.__window, commandN, None)
            if command_func:
                self.command["command"] = command_func
                self.command["plugin"] = None
                self.commands[commandN] = self.command
            else:
                self.__window.log += f"\nКоманда '{commandN}' не найдена в главном окне"

    def removeCommand(self, command_name):
        if command_name in self.commands:
            del self.commands[command_name]
            self.__window.log += f"\nUnregistered command '{command_name}'"

    def removeMenu(self, menu_id):
        if menu_id in self.menu_map:
            menu = self.menu_map.pop(menu_id)
            menu.deleteLater()
            self.__window.log += f"\nRemoved menu with ID '{menu_id}'"

    def removeShortcut(self, shortcut_info):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = next((a for a in self.__window.actions() if a.shortcut() == key_sequence), None)
        
        if action:
            self.__window.removeAction(action)
            self.__window.log += f"\nRemoved shortcut '{command}'"

    def getCommands(self):
        return self.commands

    def getCommand(self, name):
        return self.commands.get(name)
    