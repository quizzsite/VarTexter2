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
                        except Exception as e: self.__window.api.App.setLogMsg(f"Failed load plugin '{info.get('name')}' commands: {e}")
                        finally: sys.path.pop(0)
                    if info.get("menu"):
                        try:
                            menuFile = json.load(open(info.get("menu"), "r+"))
                            for menu in menuFile:
                                self.parseMenu(menuFile.get(menu), self.__window.menuBar(), pl=module)
                        except Exception as e: self.__window.api.App.setLogMsg(f"Failed load menu for '{menu}' from '{info.get('menu')}': {e}")
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
                fmenu = self.findMenu(parent, menu_id)
                if fmenu:
                    if 'children' in item:
                        self.parseMenu(item['children'], fmenu, pl)
                else:
                    menu = self.__menu_map.setdefault(menu_id, QtWidgets.QMenu(item.get('caption', 'Unnamed'), self.__window))
                    menu.setObjectName(item.get('id'))
                    parent.addMenu(menu)
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

    def executeCommand(self, c, *args, **kwargs):
        command = c
        c = self.regCommands.get(command.get("command"))
        if c:
            try:
                args = command.get("args") or args
                kwargs = command.get("kwargs") or kwargs
                out = c.get("command")(*args or [], **kwargs or {})
                self.__window.api.App.setLogMsg(f"\nExecuted command '{command}' with args '{args}', kwargs '{kwargs}'")
                if out:
                    self.__window.api.App.setLogMsg(f"\nCommand '{command}' returned '{out}'")
            except Exception as e:
                self.__window.api.App.setLogMsg(f"\nFound error in '{command}' - '{e}'.\nInfo: {c}")
        else:
            self.__window.api.App.setLogMsg(f"\nCommand '{command}' not found")
    def registerCommand(self, item, pl=None):
        if item.get('command', ""):
            self.commands.append({"command": item.get('command', ""), "plugin": pl, "args": item.get('args', []), "kwargs": item.get("kwargs", {})})
    def registerCommands(self):
        for commandInfo in self.commands:
            command = commandInfo.get("command")
            if type(command) == str:
                commandN = command
            else:
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
                    self.__window.api.App.setLogMsg(f"\nError when registering '{commandN}' from '{pl}': {e}")
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
                    self.__window.api.App.setLogMsg(f"\nCommand '{commandN}' not found")
        del self.commands

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
                found_menu = self.findMenu2(menu, menu_id)
                if found_menu:
                    return found_menu
        return None

    def findMenu2(self, menu, menu_id):
        for action in menu.actions():
            submenu = action.menu()
            if submenu:
                if submenu.objectName() == menu_id:
                    return submenu
                found_menu = self.findMenu2(submenu, menu_id)
                if found_menu:
                    return found_menu
        return None

class Tab:
    def __init__(self, w):
        self.__window = w
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

class Text:
    def __init__(self, w):
        self.__window = w
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

class Commands:
    def __init__(self, w):
        self.__window = w

class App:
    def __init__(self, w):
        self.__window = w
    def openFileDialog(e=None):
        dlg = QtWidgets.QFileDialog.getOpenFileNames(None, "Open File", "", "All Files (*);;Text Files (*.txt)")
        return dlg

    def saveFileDialog(e=None):
        dlg = QtWidgets.QFileDialog.getSaveFileName()
        return dlg

    def openDirDialog(self, e=None):
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

    def getTreeModel(self):
        return self.model

    def setTreeWidgetModel(self, dir):
        self.model = QtGui.QFileSystemModel()
        self.model.setRootPath(dir)
        self.__window.treeView.setModel(self.model)
        self.__window.treeView.setRootIndex(self.model.index(dir))
        return self.model

    def setTheme(self, theme):
        themePath = os.path.join(self.__window.themesDir, theme)
        if os.path.isfile(themePath):
            self.__window.setStyleSheet(open(themePath, "r+").read())

class FSys:
    def __init__(self, w):
        self.__window = w

    def isFile(self, path):
        return os.path.isfile(path)

class SigSlots(QtCore.QObject):

    commandsLoaded = QtCore.pyqtSignal()
    tabClosed = QtCore.pyqtSignal(int, str)
    tabChanged = QtCore.pyqtSignal()
    textChanged = QtCore.pyqtSignal()
    windowClosed = QtCore.pyqtSignal()

    treeWidgetClicked = QtCore.pyqtSignal(QtCore.QModelIndex)
    treeWidgetDoubleClicked = QtCore.pyqtSignal(QtGui.QFileSystemModel, QtCore.QModelIndex)
    treeWidgetActivated = QtCore.pyqtSignal()

    def __init__(self, w):
        super().__init__(w)
        self.__window = w

    def textChngd(self):
        tab = self.__window.tabWidget.currentWidget()
        if tab:
            self.__window.tabWidget.tabBar().setTabSaved(tab, False)

    def tabChngd(self, index):
        if index > -1:
            self.__window.setWindowTitle(f"{os.path.normpath(self.__window.api.Tab.getTabFile(index) or 'Untitled')} - {self.__window.appName}")
            if index >= 0: self.__window.encodingLabel.setText(self.__window.tabWidget.widget(index).encoding)
            self.updateEncoding()
        else:
            self.__window.setWindowTitle(self.__window.appName)
        self.tabChanged.emit()

    def updateEncoding(self):
        e = self.__window.api.Tab.getTabEncoding(self.__window.api.Tab.currentTabIndex())
        self.__window.encodingLabel.setText(e)

    def onDoubleClicked(self, index):        self.treeWidgetDoubleClicked.emit(self.__window.treeView.model(), index)

    def onClicked(self, index):        self.treeWidgetClicked.emit(index)

    def onActivated(self):        self.treeWidgetActivated.emit()

    def textChngd(self):
        tab = self.__window.tabWidget.currentWidget()
        if tab:
            self.__window.tabWidget.tabBar().setTabSaved(tab, False)

    def textChangeEvent(self, i):
        tab = self.__window.tabWidget.widget(i)
        tab.textEdit.textChanged.connect(self.textChngd)
        tab.textEdit.document().contentsChanged.connect(self.textChngd)

class VtAPI:
    def __init__(self, parent):
        self.__window = parent
        self.__version__ = self.__window.__version__
        self.Tab = Tab(self.__window)
        self.Text = Text(self.__window)
        self.SigSlots = SigSlots(self.__window)
        self.App = App(self.__window)

    def __str__(self):
        return f"""\n------------------------------VtAPI--version--{str(self.__version__)}------------------------------\nDocumentation:https://wtfidklol.com"""

    def loadThemes(self, menu):
        if os.path.isdir(self.__window.themesDir) and os.path.isfile(self.__window.mb):
            with open(self.__window.mb, "r+") as file:
                try:
                    menus = json.load(file)
                except Exception as e:
                    self.setLogMsg(f"Error when loading '{self.__window.mb}': {e}")
            themeMenu = self.__window.pl.findMenu(menu, "themes")
            if themeMenu:
                themeMenu["children"].clear()
                for theme in os.listdir(self.__window.themesDir):
                    if os.path.isfile(os.path.join(self.__window.themesDir, theme)) and theme[-1:-3] == "qss":
                        themeMenu["children"].append({"caption": theme, "command": f"setTheme {theme}"})
                json.dump(menus, open(self.__window.mb, "w+"))

    def getCommand(self, name):
        return self.__window.pl.regCommands.get(name)