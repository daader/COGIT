from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QFormLayout, QMessageBox
)
from pathlib import Path
from core.config import CogitConfig

class SettingsDialog(QDialog):
    def __init__(self, config: CogitConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cogit Settings")
        self.config = config
        self.updated_config = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Vault Path (Functions as Repo Path too)
        self.vault_input = QLineEdit(str(self.config.vault_path))
        self.vault_btn = QPushButton("Browse")
        self.vault_btn.clicked.connect(self.browse_vault)
        vault_layout = QHBoxLayout()
        vault_layout.addWidget(self.vault_input)
        vault_layout.addWidget(self.vault_btn)
        form.addRow("Vault/Repo Path:", vault_layout)
        
        # Branch
        self.branch_input = QLineEdit(self.config.branch)
        form.addRow("Branch:", self.branch_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def browse_vault(self):
        path = QFileDialog.getExistingDirectory(self, "Select Obsidian Vault", self.vault_input.text())
        if path:
            self.vault_input.setText(path)

    def save(self):
        vault_path = Path(self.vault_input.text())
        
        if not vault_path.exists():
            QMessageBox.warning(self, "Invalid Path", "Vault path does not exist.")
            return

        self.updated_config = CogitConfig(
            vault_path=vault_path,
            branch=self.branch_input.text()
        )
        self.accept()

    def get_config(self) -> CogitConfig:
        return self.updated_config
