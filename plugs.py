import sys, json, importlib
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu
from PyQt5.QtGui import QKeySequence
import os
import platform

class PluginManager:
    def __init__(self, plugin_directory: str, w):
        self.plugin_directory = plugin_directory
        self.window = w
        self.plugins = []
    
    def load_plugins(self): self._load_plugins()

    def _load_plugins(self):
        try:
            sys.path.insert(0, self.plugin_directory)
            for plugDir in os.listdir(self.plugin_directory):
                if os.path.isdir(os.path.join(self.plugin_directory, plugDir)) and os.path.isfile(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini"):
                    plugInfo = self.window.load_ini_file(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini")
                    self.plugins.append(plugInfo)
                    self.window.regAll()
        finally:
            sys.path.pop(0)

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

class DynamicMenuWithShortcuts(QMainWindow):
    def __init__(self, ini_path):
        super().__init__()
        self.setWindowTitle("Dynamic Menu with Shortcuts")
        self.setGeometry(100, 100, 600, 400)
        self.menu_map = {}
        self.commands = {}
        self.context_menu = QMenu(self)
        self.plugin_menu = QMenu("Plugins", self)
        self.pl = PluginManager("plugins", self)
        self.menuBar().addMenu(self.plugin_menu)
        
        self.constants = {
            "platform": StaticInfo.get_platform(),
            "basedir": StaticInfo.get_basedir(),
            "filedir": StaticInfo.get_filedir(__file__),
            "username": os.getlogin()
        }

        self.pl.load_plugins()

    def load_ini_file(self, ini_path):
        self.ini_path = ini_path
        config = configparser.ConfigParser()
        config.read(self.ini_path)

        self.name = config.get('DEFAULT', 'name', fallback='Unknown Plugin')
        self.version = config.get('DEFAULT', 'version', fallback='1.0')
        self.main_script = config.get('DEFAULT', 'main', fallback='')
        self.plugInfo = {"name": self.name, "version": self.version, "path": ini_path, "main": self.main_script}
        self.cm = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'cm', fallback=''))) if config.get('DEFAULT', 'cm', fallback='') else ""
        self.mb = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'mb', fallback=''))) if config.get('DEFAULT', 'mb', fallback='') else ""
        self.sc = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'sc', fallback=''))) if config.get('DEFAULT', 'sc', fallback='') else ""
        return self.plugInfo

    def regAll(self):
        if self.mb:
            self.parse_menu(json.load(open(self.mb, "r+")), self.menuBar(), pluginPath=self.ini_path)
            self.plugInfo["mb"] = self.mb

        if self.cm:
            self.parse_menu(json.load(open(self.cm, "r+")), self.context_menu, pluginPath=self.ini_path)
            self.plugInfo["cm"] = self.cm

        if self.sc:
            for shortcut in json.load(open(self.sc, "r+")):
                self.create_shortcut(shortcut)            
            self.plugInfo["sc"] = self.sc

        self.addPlugin(self.name, self.version)

    def contextMenuEvent(self, event):
        if self.context_menu:
            self.context_menu.exec_(self.mapToGlobal(event.pos()))

    def create_shortcut(self, shortcut_info):
        print(shortcut_info)
        keys = shortcut_info.get("keys", [])
        command = shortcut_info.get("command")
        args = shortcut_info.get("args", {})
        
        if not keys or not command:
            return
        
        key_sequence = QKeySequence(' '.join(keys))
        action = QAction(self)
        action.setShortcut(key_sequence)
        action.triggered.connect(lambda: self.execute_command(command, args))
        self.addAction(action)

    def parse_menu(self, data, parent, pluginPath=None):
        if isinstance(data, list):
            for item in data:
                if 'id' in item:
                    menu = self.menu_map.get(item['id'])
                    if menu is None:
                        menu = QMenu(item.get('caption', 'Unnamed'), self)
                        self.menu_map[item['id']] = menu
                        parent.addMenu(menu)
                    if 'children' in item:
                        self.parse_menu(item['children'], menu, pluginPath=pluginPath)
                else:
                    if 'children' in item:
                        submenu = QMenu(item.get('caption', 'Unnamed'), self)
                        self.parse_menu(item['children'], submenu)
                        parent.addMenu(submenu)
                    else:
                        if 'caption' in item and item['caption'] == "-":
                            parent.addSeparator()
                        else:
                            action = QAction(item.get('caption', 'Unnamed'), self)
                            if 'command' in item:
                                self.registerCommand(command=item['command'], pluginPath=pluginPath)
                                action.triggered.connect(lambda checked, cmd=item['command'], args=item.get('args', {}): self.execute_command(cmd, args))
                            parent.addAction(action)
                            if 'shortcut' in item:
                                action.setShortcut(QKeySequence(item['shortcut']))
        elif isinstance(data, dict):
            self.parse_menu([data], parent)

    def execute_command(self, command, *args):
        if self.commands.get(command): self.commands.get(command).get("command")()

    def addPlugin(self, name, version):
        plugin_info = f"{name} v{version}"
        self.plugin_menu.addAction(QAction(plugin_info, self))
    
    def registerCommand(self, command, pluginPath=None):
        commandN = command
        print(self.pl.plugins)
        if pluginPath:
            for plugin in self.pl.plugins:
                if plugin.get("path") == pluginPath:
                    print("Registering command")
                    self.command = {}
                    print(plugin.get("path"))
                    sys.path.insert(0, os.path.dirname(plugin.get("path")))
                    main_module = plugin.get("main")
                    if main_module.endswith('.py'):
                        main_module = main_module[:-3]
                    plug = importlib.import_module(main_module)
                    command = getattr(plug, commandN)
                    print(command)
                    self.command["command"] = command
                    self.command["plugin"] = plug
                    self.commands[commandN] = self.command

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DynamicMenuWithShortcuts("ini_path")
    window.show()
    sys.exit(app.exec_())
