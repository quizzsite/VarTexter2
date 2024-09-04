import os

def initAPI(api):
    global vtapi
    vtapi = api

def apiCommand(n):
    if vtapi is None:
        raise ValueError("vtapi is not initialized.")
    command = vtapi.getCommand(n)
    if command is None:
        raise ValueError(f"Command '{n}' not found.")
    return command.get("command")

def dirSet(dir=None):
    dir = dir or apiCommand("dirOpenDialog")()
    model = apiCommand("setTreeWidgetModel")(dir)

    vtapi.treeWidgetDoubleClicked.connect(fileManDClicked)

def fileManDClicked(i):
    print(i)
    # if os.path.isfile(model.filePath(i)):
        # apiCommand("openFile")([model.filePath(i)])
