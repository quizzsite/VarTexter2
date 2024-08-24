from PyQt5 import QtWidgets
import sys

class MainWindow(QtWidgets.QMainWindow):
    def closeEvent(self, event):
        dlg = QtWidgets.QMessageBox(self)
        dlg.setWindowTitle("VarTexter2 - Exiting")
        dlg.setText("File is unsaved. Do you want to close it?")
        dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

        # Настройка стилей для кнопок
        yesButton = dlg.button(QtWidgets.QMessageBox.Yes)
        noButton = dlg.button(QtWidgets.QMessageBox.No)
        cancelButton = dlg.button(QtWidgets.QMessageBox.Cancel)

        yesButton.setStyleSheet("QPushButton { color: white; }")
        noButton.setStyleSheet("QPushButton { color: white; }")
        cancelButton.setStyleSheet("QPushButton { color: white; }")
        
        dlg.setDefaultButton(cancelButton)

        # Настройка стиля для диалогового окна
        dlg.setStyleSheet("QMessageBox { background-color: black; } QLabel { color: white; }")

        # Выполнение диалогового окна и получение результата
        result = dlg.exec_()

        # Теперь правильно сравниваем результат с константами QMessageBox
        if result == QtWidgets.QMessageBox.Yes:
            print("Yes selected")  # Замени на self.MainWindow.saveFile(tab.file), если нужно сохранить файл
            # self.MainWindow.saveFile(tab.file)
        elif result == QtWidgets.QMessageBox.No:
            print("No selected")
            # tab.deleteLater()  # Удаление вкладки, если нужно
            # self.removeTab(currentIndex)
        elif result == QtWidgets.QMessageBox.Cancel:
            print("Cancel selected")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
