from classes import *
import os

recentFiles = eval(open("recent.f", "r+").read()) or []

def initAPI(api):
    global vtapi
    vtapi = api
    vtapi.tabClosed.connect(lambda index, file: addToRecent(file))

def apiCommand(n):
    return vtapi.getCommand(n).get("command")

def addToRecent(f):
    recentFiles.append(f)
    recLog = open("recent.f", "w+")
    recLog.truncate(0)
    recLog.write(str(recentFiles))
    recLog.close()

def openRecentFile(e=False):
    i = apiCommand("currentTabIndex")()
    if len(recentFiles) > 0:
        openFile([recentFiles[-1]])
        recentFiles.remove(recentFiles[-1])
        recLog = open("recent.f", "w+")
        recLog.truncate(0)
        recLog.write(str(recentFiles))
        recLog.close()
        apiCommand("setTabTitle")(i, os.path.basename(apiCommand("getTabFile")(i) or "Untitled"))
        apiCommand("setTabSaved")(i, True)

def openFile(filePath=None, encoding=None):
    if not filePath:
        filePath, _ = apiCommand("openFileDialog")()
        if not filePath:
            return
    for file in filePath:
        encoding = encoding or 'utf-8'
        apiCommand("addTab")(name=file, canSave=True)
        apiCommand("setTab")(-1)
        i = apiCommand("currentTabIndex")()
        apiCommand("setTabFile")(i, file)
        thread = FileReadThread(vtapi, file)
        thread.chunkRead = queue.Queue()

        thread.start()

        while thread.is_alive():
            try:
                chunk = thread.chunkRead.get(timeout=0.1)
                apiCommand("setTabText")(i, chunk)
            except queue.Empty:
                continue

        thread.finished.wait()
        thread.stop()
        apiCommand("setTabTitle")(i, os.path.basename(apiCommand("getTabFile")(i) or "Untitled"))
        apiCommand("setTabSaved")(i, True)

def saveFile(f=None):
    i = apiCommand("currentTabIndex")()
    text = apiCommand("getTabText")(i)
    if apiCommand("getTabCanSave")(i):
        if f:
            apiCommand("setTabFile")(i, f)
        if not apiCommand("getTabFile")(i):
            apiCommand("setTabFile")(i, apiCommand("saveFileDialog")()[0])
        if apiCommand("getTabFile")(i):
            thread = FileWriteThread(vtapi, text)
            thread.start()
            thread.finished.wait()
            thread.stop()
            apiCommand("setTabTitle")(i, os.path.basename(apiCommand("getTabFile")(i) or "Untitled"))
            apiCommand("setTabSaved")(i, True)

def saveAsFile(self):
    saveFile(apiCommand("saveFileDialog")()[0])
