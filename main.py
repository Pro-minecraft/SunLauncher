from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QSpacerItem, QSizePolicy, QPushButton
from sys import exit, argv
from uuid import uuid1
from subprocess import call
import minecraft_launcher_lib
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.utils import get_minecraft_directory
import logging
from random_username.generate import generate_username

minecraft_directory = get_minecraft_directory().replace('minecraft', 'sunlauncher')


def log():
    logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="w")
    logging.debug("A DEBUG Message")
    logging.info("An INFO")
    logging.warning("A WARNING")
    logging.error("An ERROR")
    logging.critical("A message of CRITICAL severity")


class Launch_Thread(QThread):
    launch_setup_signal = pyqtSignal(str, str)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)
    version_id = ''
    username = ''
    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username):
        self.version_id = version_id
        self.username = username

    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):
        self.state_update_signal.emit(True)
        install_minecraft_version(versionid=self.version_id,
                                  minecraft_directory=minecraft_directory,
                                  callback={'setStatus': self.update_progress_label,
                                            'setProgress': self.update_progress,
                                            'setMax': self.update_progress_max})
        if self.username == '':
            username = generate_username()[0]
        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }
        call(minecraft_launcher_lib.command.get_minecraft_command(version=self.version_id,
                                                                  minecraft_directory=minecraft_directory,
                                                                  options=options))
        self.state_update_signal.emit(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(300, 283)
        self.centralwidget = QWidget(self)
        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QtCore.QSize(256, 37))
        self.logo.setText('')
        self.logo.setPixmap(QtGui.QPixmap("assets/title.png"))
        self.logo.setScaledContents(True)
        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText("Username")
        self.version_select = QComboBox(self.centralwidget)
        for version in minecraft_launcher_lib.utils.get_version_list():
            self.version_select.addItem(version['id'])
        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)
        self.start_progress = QtWidgets.QProgressBar(self.centralwidget)
        self.start_progress.setProperty("value", 24)
        self.start_progress.setObjectName("start_progress")
        self.start_progress.setVisible(False)
        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Play')
        self.start_button.clicked.connect(self.launch_game)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.verticalLayout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.verticalLayout.addItem(self.titlespacer)
        self.verticalLayout.addWidget(self.username)
        self.verticalLayout.addWidget(self.version_select)
        self.verticalLayout.addItem(self.progress_spacer)
        self.verticalLayout.addWidget(self.start_progress_label)
        self.verticalLayout.addWidget(self.start_progress)
        self.verticalLayout.addWidget(self.start_button)
        self.launch_thread = Launch_Thread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.setCentralWidget(self.centralwidget)

    def state_update(self, value):
        self.start_button.setDisabled(value)
        self.start_progress.setVisible(value)
        self.start_progress.setVisible(value)

    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label)

    def launch_game(self):
        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), self.username.text())
        self.launch_thread.start()


if __name__ == "__main__":
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())
