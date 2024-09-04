import importlib.util
import sys
import os

def importModule(path, n):
    spec = importlib.util.spec_from_file_location(n, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[n] = module
    spec.loader.exec_module(module)
    return module

# Пример использования
plugin_path_1 = r'plugins\Googler\googler.py'
plugin_path_2 = 'plugins/AnotherPlugin/googler.py'

# Импортируем файлы под разными уникальными именами
try:
    plugin_module_1 = import_module_with_n(plugin_path_1, 'GooglerPlugin1')
    # plugin_module_2 = import_module_with_n(plugin_path_2, 'GooglerPlugin2')
    print(f"Модули успешно импортированы:")
    print(f" - {plugin_module_1} как GooglerPlugin1")
    # print(f" - {plugin_module_2} как GooglerPlugin2")
except (FileNotFoundError, ImportError) as e:
    print(f"Ошибка при импорте модуля: {e}")
