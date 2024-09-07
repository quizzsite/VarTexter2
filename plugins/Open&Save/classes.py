import threading
import queue
import chardet
import time

class FileReadThread(threading.Thread):
    def __init__(self, vtapi, file_path):
        super(FileReadThread, self).__init__()
        self.vtapi = vtapi
        self.file_path = file_path
        self._is_running = True
        self.chunkRead = queue.Queue()
        self.finishedReading = threading.Event()
        self.finished = threading.Event()

    def run(self):
        filep = open(self.file_path, 'rb')
        m = chardet.detect(filep.read(1024 * 3))
        fencoding = m["encoding"]
        filep.close()

        if fencoding:
            file = open(self.file_path, 'r', encoding=fencoding)
            self.vtapi.setTabEncoding(self.vtapi.currentTabIndex(), fencoding.upper())
        else:
            file = open(self.file_path, 'rb')
            fencoding = "BYTES"
            self.vtapi.setTabEncoding(self.vtapi.currentTabIndex(), fencoding)

        try:
            while self._is_running:
                chunk = file.read(1024 * 400)
                if fencoding == "BYTES":
                    hex_representation = chunk.hex()
                    chunk = ' '.join(hex_representation[i:i+4] for i in range(0, len(hex_representation), 4))
                if not chunk:
                    break
                self.chunkRead.put(str(chunk))
                self._sleep(3)
        finally:
            file.close()
            self.finishedReading.set()
            self.finished.set()

    def stop(self):
        self._is_running = False
        self.vtapi.setTabSaved(self.vtapi.currentTabIndex(), True)
        self.vtapi.textChangeEvent(self.vtapi.currentTabIndex())

    def _sleep(self, milliseconds):
        time.sleep(milliseconds / 1000)

class FileWriteThread(threading.Thread):
    def __init__(self, vtapi, text):
        super(FileWriteThread, self).__init__()
        self.vtapi = vtapi
        self.text = text
        self._is_running = True
        self.finished = threading.Event()

    def run(self):
        with open(self.vtapi.getTabFile(self.vtapi.currentTabIndex()), "w", encoding=self.vtapi.getTabEncoding(self.vtapi.currentTabIndex())) as f:
            f.truncate(0)
            f.write(self.text)
            f.close()
        self.finished.set()

    def stop(self):
        self._is_running = False
        self.vtapi.setTabSaved(self.vtapi.currentTabIndex(), True)
        self.vtapi.textChangeEvent(self.vtapi.currentTabIndex())
