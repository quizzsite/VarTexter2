'''
Package Manager for VT2

Console->Package Manager-?List->Install->Unzip=>Move->Import

Plugins will be downloaded from idklolwtf.com
'''
import urllib.request
import urllib, uuid, os, shutil
import zipfile

class PackageManager:
    def __init__(self, window, packagesDir) -> None:
        self.window = window
        self.packagesDir = packagesDir
        self.tempDir = os.getenv().get("TEMP")

    def tempname(self, n):
        return "vt-"+str(uuid.uuid4())[:n+1]+"-install"
    
    def install(self, type, url):
        tempDirName = self.tempname()
        path = os.path.join(self.tempDir, tempDirName)
        os.makedirs(path)

        filePath = os.path.join(path, "package.zip")
        urllib.request.urlretrieve(url, filePath)
        f = zipfile.ZipFile(filePath)
        f.extractall(path)
        os.remove(filePath)
        shutil.move(path, os.path.join(self.packagesDir, type))
        # os.rename(os.path.join(self.packagesDir, type, tempDirName), "name")

    def uninstall(self, dir):
        if os.path.isdir(dir):
            os.rmdir(dir)

    def search(self, name):
        pass
    
p = PackageManager("")
print(p.tempname(7))