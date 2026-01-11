from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPalette

from core.config import CogitConfig, save_config
from core.git import GitManager
from core.status import StatusChecker, RepoState
from core.session import get_session_start_message, get_session_end_message
from ui.settings_dialog import SettingsDialog
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self, config: CogitConfig):
        super().__init__()
        self.setWindowTitle("Cogit")
        self.resize(500, 600)
        self.config = config
        
        # Initialize Core objects
        self.init_core()

        self.setup_ui()
        
        # Initial status check
        self.check_status()
        self.log("Cogit started.")

    def init_core(self):
        try:
            # We use vault_path (alias repo_path) for git operations
            self.git_manager = GitManager(self.config.vault_path)
            self.status_checker = StatusChecker(self.git_manager)
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize Git: {e}")
            self.git_manager = None
            self.status_checker = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)

        # Header / Info
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        
        self.vault_label = QLabel(f"Vault: {self.config.vault_path}")
        self.branch_label = QLabel(f"Branch: {self.config.branch}")
        
        info_layout.addWidget(self.vault_label)
        info_layout.addWidget(self.branch_label)
        layout.addWidget(info_frame)

        # Status Section
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        
        self.status_indicator = QLabel("● Ready")
        font = self.status_indicator.font()
        font.setPointSize(14)
        font.setBold(True)
        self.status_indicator.setFont(font)
        
        self.last_sync_label = QLabel("Last sync: Never")
        
        status_layout.addWidget(self.status_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.last_sync_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_frame)

        # Actions
        self.check_btn = QPushButton("Check Status")
        self.check_btn.setMinimumHeight(40)
        self.check_btn.clicked.connect(self.check_status)
        layout.addWidget(self.check_btn)

        action_layout = QHBoxLayout()
        self.pull_btn = QPushButton("Pull from GitHub")
        self.pull_btn.setMinimumHeight(40)
        self.pull_btn.clicked.connect(self.pull)
        
        self.push_btn = QPushButton("Push to GitHub")
        self.push_btn.setMinimumHeight(40)
        self.push_btn.clicked.connect(self.push)
        
        action_layout.addWidget(self.pull_btn)
        action_layout.addWidget(self.push_btn)
        layout.addLayout(action_layout)

        # Log
        layout.addWidget(QLabel("Log:"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        # Footer Actions
        footer_layout = QHBoxLayout()
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        self.quit_btn = QPushButton("Quit")
        self.quit_btn.clicked.connect(self.close)
        
        footer_layout.addWidget(self.settings_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(self.quit_btn)
        layout.addLayout(footer_layout)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")

    def update_status_ui(self, state: RepoState, message: str):
        self.status_indicator.setText(f"● {message}")
        color = "black"
        if state == RepoState.UP_TO_DATE:
            color = "green"
        elif state == RepoState.REMOTE_AHEAD:
            color = "blue"
        elif state == RepoState.LOCAL_AHEAD:
            color = "orange"
        elif state == RepoState.DIVERGED or state == RepoState.ERROR:
            color = "red"
        
        self.status_indicator.setStyleSheet(f"color: {color};")
        self.log(f"Status: {message}")

    def check_status(self):
        if not self.status_checker:
            self.update_status_ui(RepoState.ERROR, "Git not initialized")
            return

        self.log("Checking status...")
        
        result = self.status_checker.check_status()
        if result.last_sync:
             self.last_sync_label.setText(f"Last sync: {result.last_sync}")
        
        self.update_status_ui(result.state, result.message)

    def pull(self):
        if not self.git_manager: return
        self.log("Pulling changes...")
        try:
            result = self.git_manager.pull()
            self.log(result)
            self.check_status()
        except Exception as e:
            self.log(f"Error pulling: {e}")
            QMessageBox.critical(self, "Pull Error", str(e))

    def push(self):
        if not self.git_manager: return
        self.log("Pushing changes...")
        try:
            # Commit first
            msg = get_session_end_message() # Using session end as generic generic commit for now
            commit_res = self.git_manager.commit_all(msg)
            self.log(commit_res)
            
            # Push
            push_res = self.git_manager.push()
            self.log(push_res)
            
            self.last_sync_label.setText(f"Last sync: {datetime.now().strftime('%H:%M')}")
            self.check_status()
        except Exception as e:
            self.log(f"Error pushing: {e}")
            QMessageBox.critical(self, "Push Error", str(e))

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            if new_config:
                self.config = new_config
                save_config(self.config)
                self.init_core() # Re-init with new paths
                self.update_ui_config()
                self.log("Settings saved.")
                self.check_status()

    def update_ui_config(self):
        self.vault_label.setText(f"Vault: {self.config.vault_path}")
        self.branch_label.setText(f"Branch: {self.config.branch}")
