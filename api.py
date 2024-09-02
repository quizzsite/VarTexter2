from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
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

    def __init__(self, parent):
        super().__init__(parent)
        self.__window_ref = weakref.ref(parent)
        self.menu_map = {}
        self.commands = {}

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
            self.parseMenu(json.load(open(self.mb, "r+")), self.__window_ref().menuBar(), pluginPath=self.ini_path)
            self.plugInfo["mb"] = self.mb


        if self.cm:
            self.parseMenu(json.load(open(self.cm, "r+")), self.__window_ref().contextMenu, pluginPath=self.ini_path)
            self.plugInfo["cm"] = self.cm

        if self.tcm:
            self.parseMenu(json.load(open(self.tcm, "r+")), self.__window_ref().textContextMenu, pluginPath=self.ini_path)
            self.plugInfo["tcm"] = self.tcm

        if self.sc:
            for shortcut in json.load(open(self.sc, "r+")):
                self.createShortcut(shortcut, pluginPath=self.ini_path)            
            self.plugInfo["sc"] = self.sc

    def createShortcut(self, shortcut_info, pluginPath=None):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        text = shortcut_info.get("text", "Action")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = QtWidgets.QAction(self.__window_ref())
        action.setText(text)
        action.setShortcut(key_sequence)
        self.registerCommand(command, pluginPath=pluginPath)
        action.triggered.connect(lambda: self.executeCommand(command))
        self.__window_ref().addAction(action)

    def parseMenu(self, data, parent, pluginPath=None):
        if isinstance(data, dict):
            data = [data]

        for item in data:
            menu_id = item.get('id')
            if menu_id:
                menu = self.menu_map.setdefault(menu_id, QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window_ref()))
                parent.addMenu(menu)
                if 'children' in item:
                    self.parseMenu(item['children'], menu, pluginPath)
            else:
                if 'children' in item:
                    submenu = QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window_ref())
                    self.parseMenu(item['children'], submenu)
                    parent.addMenu(submenu)
                else:
                    if item.get('caption') == "-":
                        parent.addSeparator()
                    else:
                        action = QtWidgets.QAction(item.get('caption', 'Unnamed'), self.__window_ref())
                        if 'command' in item:
                            self.registerCommand(item['command'], pluginPath)
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
    def executeCommand(self, command, *args):
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
                    self.__window_ref().log += f"\nCommand '{command}' returned '{out}'"
            except Exception as e:
                self.__window_ref().log += f"\nFound error in '{command}' - '{e}'.\nInfo: {c}"
    def initAPI(self, f):
        sys.path.insert(0, os.path.dirname(f.get("path")))
        main_module = f.get("main")
        if main_module.endswith('.py'):
            main_module = main_module[:-3]
            plug = importlib.import_module(main_module)
            if hasattr(plug, "initAPI"):
                plug.initAPI(self.__window_ref().api)
            del plug
    def registerCommand(self, command, pluginPath=None):
        commandN = command.split()[0]
        if pluginPath:
            for plugin in self.__window_ref().pl.plugins:
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
                        self.__window_ref().log += f"\nFound error in '{main_module}' - {e}"

        else:
            self.command = {}
            command = getattr(self.__window_ref(), commandN)
            self.command["command"] = command
            self.command["plugin"] = None
            self.commands[commandN] = self.command

    def removeCommand(self, command_name):
        if command_name in self.commands:
            del self.commands[command_name]
            self.__window_ref().log += f"\nUnregistered command '{command_name}'"

    def removeMenu(self, menu_id):
        if menu_id in self.menu_map:
            menu = self.menu_map.pop(menu_id)
            menu.deleteLater()
            self.__window_ref().log += f"\nRemoved menu with ID '{menu_id}'"

    def removeShortcut(self, shortcut_info):
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        
        if not keys or not command:
            return
        
        key_sequence = QtGui.QKeySequence(' '.join(keys))
        action = next((a for a in self.__window_ref().actions() if a.shortcut() == key_sequence), None)
        
        if action:
            self.__window_ref().removeAction(action)
            self.__window_ref().log += f"\nRemoved shortcut '{command}'"

    def getCommands(self):
        return self.commands

    def getCommand(self, name):
        return self.commands.get(name)
    