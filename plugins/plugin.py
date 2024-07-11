from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget
from plugs import PluginInterface

class Plugin(PluginInterface):
    def init_plugin(self, proxy):
        # Создание текстового поля для консоли
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        
        # Добавление консоли в главный интерфейс
        proxy.add_widget(self.console)
        
        # Пример вывода текста в консоль
        self.console.append("Console initialized!")

    def log(self, message):
        """Метод для вывода сообщений в консоль"""
        self.console.append(message)
