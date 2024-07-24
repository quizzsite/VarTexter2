import sys, json, importlib
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu
from PyQt5.QtGui import QKeySequence
import os
import platform

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
        
        self.constants = {
            "platform": StaticInfo.get_platform(),
            "basedir": StaticInfo.get_basedir(),
            "filedir": StaticInfo.get_filedir(__file__),
            "username": os.getlogin()
        }

    def load_ini_file(self, ini_path):
        config = configparser.ConfigParser()
        config.read(ini_path)

        self.name = config.get('DEFAULT', 'name', fallback='Unknown Plugin')
        self.version = config.get('DEFAULT', 'version', fallback='1.0')
        self.main_script = config.get('DEFAULT', 'main', fallback='')
        self.cm = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'cm', fallback=''))) if config.get('DEFAULT', 'cm', fallback='') else ""
        self.mb = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'mb', fallback=''))) if config.get('DEFAULT', 'mb', fallback='') else ""
        self.sc = str(os.path.join(os.path.dirname(ini_path), config.get('DEFAULT', 'sc', fallback=''))) if config.get('DEFAULT', 'sc', fallback='') else ""


        self.create_base_menus()
        self.create_context_menu()
        self.create_shortcuts()

        self.add_plugin_info_to_menu()

    def create_base_menus(self):
        if not self.mb:
            return
        base_menus = json.load(open(self.mb, "r+"))
        self.menu_bar = self.menuBar()
        self.parse_menu(base_menus, self.menu_bar)

    def create_context_menu(self):
        if not self.cm:
            return
        context_menu_data = json.load(open(self.cm, "r+"))
        self.context_menu = QMenu(self)
        print(context_menu_data)
        self.parse_menu(context_menu_data, self.context_menu)

    def contextMenuEvent(self, event):
        if self.context_menu:
            self.context_menu.exec_(self.mapToGlobal(event.pos()))

    def create_shortcuts(self):
        if not self.sc:
            return
        for shortcut in json.load(open(self.sc, "r+")):
            self.create_shortcut(shortcut)

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

    def parse_menu(self, data, parent):
        if isinstance(data, list):
            for item in data:
                if 'id' in item:
                    menu = self.menu_map.get(item['id'])
                    if menu is None:
                        menu = QMenu(item.get('caption', 'Unnamed'), self)
                        self.menu_map[item['id']] = menu
                        parent.addMenu(menu)
                    if 'children' in item:
                        self.parse_menu(item['children'], menu)
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
                                action.triggered.connect(lambda checked, cmd=item['command'], args=item.get('args', {}): self.execute_command(cmd, args))
                            parent.addAction(action)
                            if 'shortcut' in item:
                                action.setShortcut(QKeySequence(item['shortcut']))
        elif isinstance(data, dict):
            self.parse_menu([data], parent)

    def execute_command(self, command, args):
        if command == "open_file":
            self.open_file(args.get("file", ""))
        elif command == "new_file":
            self.new_file(args.get("file", ""))
        elif command == "exit_app":
            self.close()
        elif command == "undo":
            print("Undo action triggered")
        elif command == "redo":
            print("Redo action triggered")
        elif command == "advanced_new_file_new":
            self.advanced_new_file_new(args)
        elif command == "insert":
            self.insert(args)
        else:
            print(f"Unknown command: {command}")

    def open_file(self, filepath):
        print(f"Opening file: {filepath}")

    def new_file(self, filename):
        print(f"Creating new file: {filename}")

    def advanced_new_file_new(self, args):
        is_python = args.get("is_python", False)
        if is_python:
            print("Creating a new Python file.")
        else:
            print("Creating a new file.")

    def insert(self, args):
        characters = args.get("characters", "")
        print(f"Inserting characters: {characters}")

    def add_plugin_info_to_menu(self):
        plugin_info = f"{self.name} ({self.version})"
        plugin_menu = QMenu("Plugins", self)
        plugin_menu.addAction(QAction(plugin_info, self))
        self.menuBar().addMenu(plugin_menu)

class PluginManager:
    def __init__(self, plugin_directory: str, w):
        self.plugin_directory = plugin_directory
        self.window = w
        self.plugins = []
        self._load_plugin()

    def _load_plugin(self):
        try:
            sys.path.insert(0, self.plugin_directory)
            for plugDir in os.listdir(self.plugin_directory):
                if os.path.isdir(os.path.join(self.plugin_directory, plugDir)) and os.path.isfile(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini"):
                    self.window.load_ini_file(f"{os.path.join(self.plugin_directory, plugDir)}\config.ini")
        except Exception as e:
            print(f'Error loading plugin: {e}')
        finally:
            sys.path.pop(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DynamicMenuWithShortcuts("ini_path")
    plugs = PluginManager("plugins", window)
    window.show()
    sys.exit(app.exec_())
