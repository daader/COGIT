from dataclasses import dataclass
from pathlib import Path
import os
import tomlkit
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "cogit"
CONFIG_FILE = CONFIG_DIR / "config.toml"

@dataclass
class CogitConfig:
    vault_path: Path
    branch: str = "main"

    @property
    def repo_path(self) -> Path:
        """Alias for vault_path, since they are now the same."""
        return self.vault_path

def load_config() -> Optional[CogitConfig]:
    """Loads configuration from CONFIG_FILE."""
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = tomlkit.load(f)
            
        vault_path = Path(data.get("vault", {}).get("path", ""))
        repo_data = data.get("git", {})
        branch = repo_data.get("branch", "main")

        if not str(vault_path) or str(vault_path) == ".":
             return None 

        return CogitConfig(
            vault_path=vault_path,
            branch=branch
        )
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def save_config(config: CogitConfig):
    """Saves configuration to CONFIG_FILE."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    doc = tomlkit.document()
    
    vault_table = tomlkit.table()
    vault_table["path"] = str(config.vault_path)
    doc["vault"] = vault_table

    git_table = tomlkit.table()
    git_table["branch"] = config.branch
    doc["git"] = git_table

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        tomlkit.dump(doc, f)
