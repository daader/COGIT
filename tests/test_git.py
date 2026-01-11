import pytest
from pathlib import Path
import git
from core.git import GitManager

@pytest.fixture
def mock_repo(mocker):
    return mocker.MagicMock(spec=git.Repo)

def test_git_manager_init(mock_repo, mocker):
    mocker.patch("git.Repo", return_value=mock_repo)
    manager = GitManager(Path("/tmp/repo"))
    assert manager.get_repo() == mock_repo

def test_has_changes(mock_repo, mocker):
    mocker.patch("git.Repo", return_value=mock_repo)
    manager = GitManager(Path("/tmp/repo"))
    
    mock_repo.is_dirty.return_value = True
    assert manager.has_changes() is True

    mock_repo.is_dirty.return_value = False
    assert manager.has_changes() is False

def test_commit_all(mock_repo, mocker):
    mocker.patch("git.Repo", return_value=mock_repo)
    manager = GitManager(Path("/tmp/repo"))
    mock_repo.is_dirty.return_value = True
    
    msg = "test commit"
    manager.commit_all(msg)
    
    mock_repo.git.add.assert_called_with(A=True)
    mock_repo.index.commit.assert_called_with(msg)

def test_commit_no_changes(mock_repo, mocker):
    mocker.patch("git.Repo", return_value=mock_repo)
    manager = GitManager(Path("/tmp/repo"))
    mock_repo.is_dirty.return_value = False
    
    result = manager.commit_all("msg")
    assert result == "No changes to commit."
    mock_repo.index.commit.assert_not_called()
