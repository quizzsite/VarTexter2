import os
import importlib
import sys
from PyQt6.QtWidgets import QWidget

class PluginInterface:
    def __init__(self):
        pass

    def init_plugin(self, proxy):
        """Инициализация плагина, при этом proxy — это прокси-класс, предоставляемый приложением"""
        raise NotImplementedError("Plugin must implement 'init_plugin' method")

class WindowProxy:
    def __init__(self, main_window):
        self._main_window = main_window

    def add_widget(self, widget, tab_index=0):
        tab = self._main_window.tabWidget.widget(tab_index)
        if tab:
            tab.layout().addWidget(widget)

    def set_tab_text(self, tab_index, text):
        self._main_window.centralwidget.setTabText(tab_index, text)

    def get_tab_count(self):
        return self._main_window.tabWidget.count()

class PluginManager:
    def __init__(self, plugin_directory: str, proxy):
        self.plugin_directory = plugin_directory
        self.proxy = proxy
        self.plugins = []

    def load_plugins(self):
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith(".py"):
                plugin_name = filename[:-3]
                self._load_plugin(plugin_name)

    def _load_plugin(self, plugin_name: str):
        try:
            sys.path.insert(0, self.plugin_directory)
            module = importlib.import_module(plugin_name)
            if hasattr(module, 'Plugin') and issubclass(module.Plugin, PluginInterface):
                plugin_instance = module.Plugin()
                plugin_instance.init_plugin(self.proxy)
                self.plugins.append(plugin_instance)
                print(f'Plugin {plugin_name} loaded successfully')
            else:
                print(f'Plugin {plugin_name} does not conform to the PluginInterface')
        except Exception as e:
            print(f'Error loading plugin {plugin_name}: {e}')
        finally:
            sys.path.pop(0)