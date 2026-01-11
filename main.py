import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from core.config import load_config, CogitConfig, save_config
from ui.main_window import MainWindow
from ui.settings_dialog import SettingsDialog

def setup_ignored_files(vault_path: Path):
    """Ensures .obsidian workspace files are ignored."""
    gitignore = vault_path / ".gitignore"
    
    # Read template
    try:
        with open("ignore/gitignore_template", "r") as f:
            template_lines = f.readlines()
    except FileNotFoundError:
        # Fallback if running from a different cwd or packed
        template_lines = [
            "\n# Cogit managed ignores\n",
            ".obsidian/workspace*\n",
            ".obsidian/cache\n",
            ".obsidian/plugins/*/data.json\n"
        ]

    # Check if lines exist
    current_content = ""
    if gitignore.exists():
        with open(gitignore, "r", encoding="utf-8") as f:
            current_content = f.read()
    
    with open(gitignore, "a", encoding="utf-8") as f:
        if "# Cogit managed ignores" not in current_content:
            f.write("\n")
            f.writelines(template_lines)

def main():
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    
    config = load_config()
    
    # If no config (first run), show Settings Dialog to prompt for Vault/Repo
    if not config:
        # Default config placeholder
        temp_config = CogitConfig(
            vault_path=Path.home() / "Documents/Obsidian Vault",
            branch="main"
        )
        # SettingsDialog needs config to populate
        dialog = SettingsDialog(temp_config)
        if dialog.exec():
            config = dialog.get_config()
            save_config(config)
        else:
            sys.exit(0) # Cancelled

    if config:
        # One-time setup
        setup_ignored_files(config.vault_path)

        # Set App Icon
        icon_path = Path(__file__).parent / "ui" / "resources" / "icon.png"
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))

        window = MainWindow(config)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
