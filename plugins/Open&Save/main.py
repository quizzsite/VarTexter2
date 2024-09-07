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
    i = vtapi.currentTabIndex()
    if len(recentFiles) > 0:
        openFile([recentFiles[-1]])
        recentFiles.remove(recentFiles[-1])
        recLog = open("recent.f", "w+")
        recLog.truncate(0)
        recLog.write(str(recentFiles))
        recLog.close()
        vtapi.setTabTitle(i, os.path.basename(vtapi.getTabFile(i) or "Untitled"))
        vtapi.setTabSaved(i, True)

def openFile(filePath=None, encoding=None):
    if not filePath:
        filePath, _ = vtapi.openFileDialog()
        if not filePath:
            return
    for file in filePath:
        encoding = encoding or 'utf-8'
        apiCommand("addTab")(name=file, canSave=True)
        vtapi.setTab(-1)
        i = vtapi.currentTabIndex()
        vtapi.setTabFile(i, file)
        thread = FileReadThread(vtapi, file)
        thread.chunkRead = queue.Queue()

        thread.start()

        while thread.is_alive():
            try:
                chunk = thread.chunkRead.get(timeout=0.1)
                vtapi.setTabText(i, chunk)
            except queue.Empty:
                continue

        thread.finished.wait()
        thread.stop()
        vtapi.setTabTitle(i, os.path.basename(vtapi.getTabFile(i) or "Untitled"))
        vtapi.setTabSaved(i, True)

def saveFile(f=None):
    i = vtapi.currentTabIndex()
    text = vtapi.getTabText(i)
    if vtapi.getTabCanSave(i):
        if f:
            vtapi.setTabFile(i, f)
        if not vtapi.getTabFile(i):
            vtapi.setTabFile(i, vtapi.saveFileDialog()[0])
        if vtapi.getTabFile(i):
            thread = FileWriteThread(vtapi, text)
            thread.start()
            thread.finished.wait()
            thread.stop()
            vtapi.setTabTitle(i, os.path.basename(vtapi.getTabFile(i) or "Untitled"))
            vtapi.setTabSaved(i, True)

def saveAsFile():
    saveFile(vtapi.saveFileDialog()[0])
