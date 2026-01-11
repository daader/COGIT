import pytest
from pathlib import Path
from core.config import CogitConfig, save_config, load_config, CONFIG_FILE

def test_save_and_load_config(mocker, tmp_path):
    # Mock CONFIG_FILE to point to our temp directory
    mock_config_file = tmp_path / "config.toml"
    mocker.patch("core.config.CONFIG_FILE", mock_config_file)
    mocker.patch("core.config.CONFIG_DIR", tmp_path)

    config = CogitConfig(
        vault_path=Path("/tmp/vault"),
        branch="develop"
    )

    save_config(config)
    
    assert mock_config_file.exists()

    loaded = load_config()
    assert loaded is not None
    assert loaded.vault_path == Path("/tmp/vault")
    # Verify alias works
    assert loaded.repo_path == Path("/tmp/vault")
    assert loaded.branch == "develop"

def test_load_nonexistent_config(mocker, tmp_path):
    mock_config_file = tmp_path / "nonexistent.toml"
    mocker.patch("core.config.CONFIG_FILE", mock_config_file)

    loaded = load_config()
    assert loaded is None
