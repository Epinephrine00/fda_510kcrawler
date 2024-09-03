
from PyQt5.QtWidgets import *      
from PyQt5.QtCore import Qt as Qt
from PyQt5.QtCore import QDate as QDate
from ui import Ui_MainWindow as ui
import sys


class MainWindow(QMainWindow, ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.pushButton.clicked.connect(self.saveParameters)

        self.show()

    def closeEvent(self, event):
        print('closing...')
        event.accept()

    def saveParameters(self):
        applicantName = self.lineEdit.text()
        timePeriod1 = self.spinBox.value()
        timePeriod2 = self.spinBox_2.value()
        timePeriod3 = self.spinBox_3.value()
        print(applicantName)
        print(timePeriod1)
        print(timePeriod2)
        print(timePeriod3)




if __name__ == "__main__":
    isDebuging = True
    
    app = QApplication(sys.argv)
    myWindow = MainWindow()
    app.exec_()