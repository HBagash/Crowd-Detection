from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from detection_window import DetectionWindow

class SettingsWindow(QMainWindow):
    def __init__(self, token):
        super(SettingsWindow, self).__init__()
        loadUi('UI/settings_window.ui', self)

        self.token = token
        self.detection_window = None  # Initialize with None

        self.pushButton.clicked.connect(self.go_to_detection)

        self.popup = QMessageBox()
        self.popup.setWindowTitle("Failed")
        self.popup.setText("Field must not be empty.")

    def displayInfo(self):
        self.show()

    def go_to_detection(self):
        if self.location_input.text() == '' or self.sendTo_input.text() == '':
            self.popup.exec_()
        else:
            # Check if detection_window is None or not visible, then create it
            if not self.detection_window or not self.detection_window.isVisible():
                self.detection_window = DetectionWindow()
                self.detection_window.create_detection_instance(
                    self.token, 
                    self.location_input.text(), 
                    self.sendTo_input.text()
                )
                self.detection_window.start_detection()
            else:
                print('Detection window is already open!')

    def closeEvent(self, event):
        if self.detection_window and self.detection_window.isVisible():
            self.detection_window.detection.running = False
            self.detection_window.close()
        event.accept()
