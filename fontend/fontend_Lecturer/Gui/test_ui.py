from PyQt5.QtWidgets import QMainWindow, QApplication, QHeaderView, QPushButton, QComboBox, QMenu, QSizeGrip ,QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSlot, QEventLoop, QTimer, QPropertyAnimation, QEasingCurve, QThread , pyqtSignal

from Ui_login import Ui_MainWindow
# from Ui_home import Ui_MainWindow
class login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.show()
        self.ui.pushButton_Signin.clicked.connect(self.Testvalua)
    def Testvalua(self):
        username  = self.ui.lineEdit_User.text()   ; password = self.ui.lineEdit_Pass.text()
        print(f'{username}-{password}')
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main = login()
    sys.exit(app.exec_())        