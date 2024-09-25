from PyQt6 import QtWidgets, QtCore, QtGui
import os, sys, configparser, json, importlib

def importModule(path, n):
    spec = importlib.util.spec_from_file_location(n, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[n] = module
    spec.loader.exec_module(module)
    return module

class PluginManager:
    def __init__(self, plugin_directory: str, w):
        self.plugin_directory = plugin_directory
        self.__window = w
        self.__menu_map = {}
        self.commands = []
        self.regCommands = {}
        self.dPath = None
    
    def load_plugins(self):
        try:
            self.dPath = os.getcwd()
            sys.path.insert(0, self.plugin_directory)
            for plugDir in os.listdir(self.plugin_directory):
                fullPath = os.path.join(self.plugin_directory, plugDir)
                os.chdir(fullPath)
                if os.path.isdir(fullPath) and os.path.isfile(f"config.ini"):
                    module = None
                    info = self.initPlugin(os.path.join(fullPath, "config.ini"))
                    if info.get("main"):
                        pyFile = info.get("main")
                        try:
                            sys.path.insert(0, fullPath)
                            module = importModule(pyFile, info.get("name") + "Plugin")
                            if hasattr(module, "initAPI"):
                                module.initAPI(self.__window.api)
                        except Exception as e: self.__window.api.setLogMsg(f"Failed load plugin '{info.get('name')}' commands: {e}")
                        finally: sys.path.pop(0)
                    if info.get("menu"):
                        try:
                            menuFile = json.load(open(info.get("menu"), "r+"))
                            for menu in menuFile:
                                self.parseMenu(menuFile.get(menu), self.__window.menuBar(), pl=module)
                        except Exception as e: self.__window.api.setLogMsg(f"Failed load menu for '{menu}' from '{info.get('menu')}': {e}")
        finally:
            os.chdir(self.dPath)
            del self.dPath
                        
    def initPlugin(self, path):
        config = configparser.ConfigParser()
        config.read(path)

        self.name = config.get('DEFAULT', 'name', fallback='Unknown')
        self.version = config.get('DEFAULT', 'version', fallback='1.0')
        self.mainFile = config.get('DEFAULT', 'main', fallback='')
        self.menuFile = config.get('DEFAULT', 'menu', fallback='')

        return {"name": self.name, "version": self.version, "main": self.mainFile, "menu": self.menuFile}
    
    def parseMenu(self, data, parent, pl=None):
        if isinstance(data, dict):
            data = [data]

        for item in data:
            if item.get('caption') == "-":
                parent.addSeparator()
                continue
            menu_id = item.get('id')
            if menu_id:
                fmenu = self.__window.api.findMenu(parent, menu_id)
                if fmenu:
                    if 'children' in item:
                        self.parseMenu(item['children'], fmenu, pl)
                else:
                    menu = self.__menu_map.setdefault(menu_id, QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window))
                    menu.setObjectName(item.get('id'))
                    print(parent.objectName())
                    parent.addMenu(menu)
                    print(item.get("caption"))
                    if 'children' in item:
                        self.parseMenu(item['children'], menu, pl)
            else:
                action = QtGui.QAction(item.get('caption', 'Unnamed'), self.__window)
                if 'command' in item:
                    args = item.get("args")
                    kwargs = item.get("kwargs")
                    self.commands.append({"command": item['command'], "plugin": pl, "args": args, "kwargs": kwargs})
                    action.triggered.connect(lambda checked, cmd=item['command']: 
                        self.executeCommand(
                            cmd
                        )
                    )
                parent.addAction(action)
                if 'shortcut' in item:
                    action.setShortcut(QtGui.QKeySequence(item['shortcut']))
                if 'checkable' in item:
                    action.setCheckable(item['checkable'])

    def executeCommand(self, c):
        command = c
        c = self.regCommands.get(command.get("command"))
        if c:
            try:
                args = command.get("args")
                kwargs = command.get("kwargs")
                out = c.get("command")(*args or [], **kwargs or {})
                self.__window.api.setLogMsg(f"\nExecuted command '{command}' with args '{args}', kwargs '{kwargs}'")
                if out:
                    self.__window.api.setLogMsg(f"\nCommand '{command}' returned '{out}'")
            except Exception as e:
                self.__window.api.setLogMsg(f"\nFound error in '{command}' - '{e}'.\nInfo: {c}")
        else:
            self.__window.api.setLogMsg(f"\nCommand '{command}' not found")

    def registerCommands(self):
        for commandInfo in self.commands:
            command = commandInfo.get("command")
            commandN = command.get("command")
            pl = commandInfo.get("plugin")
            
            args = commandInfo.get("args", [])
            kwargs = commandInfo.get("kwargs", {})

            if pl:
                try:
                    command_func = getattr(pl, commandN)
                    self.regCommands[commandN] = {
                        "command": command_func,
                        "args": args,
                        "kwargs": kwargs,
                        "plugin": pl
                    }
                except (ImportError, AttributeError, TypeError) as e:
                    self.__window.api.setLogMsg(f"\nError when registering '{commandN}' from '{pl}': {e}")
            else:
                command_func = getattr(self.__window, commandN, None)
                if command_func:
                    self.regCommands[commandN] = {
                        "command": command_func,
                        "args": args,
                        "kwargs": kwargs,
                        "plugin": None
                    }
                else:
                    self.__window.api.setLogMsg(f"\nCommand '{commandN}' not found")
        del self.commands
            
