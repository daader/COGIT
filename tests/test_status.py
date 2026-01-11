import pytest
from core.status import StatusChecker, RepoState
from core.git import GitManager

@pytest.fixture
def mock_git_manager(mocker):
    return mocker.MagicMock(spec=GitManager)

def test_status_up_to_date(mock_git_manager, mocker):
    checker = StatusChecker(mock_git_manager)
    repo = mocker.MagicMock()
    mock_git_manager.get_repo.return_value = repo
    mock_git_manager.has_changes.return_value = False
    
    # Mock branch commits
    repo.active_branch.commit = "hash1"
    repo.active_branch.tracking_branch.return_value.commit = "hash1" # Same commit
    
    status = checker.check_status()
    assert status.state == RepoState.UP_TO_DATE

def test_status_dirty_working_tree(mock_git_manager, mocker):
    checker = StatusChecker(mock_git_manager)
    repo = mocker.MagicMock()
    mock_git_manager.get_repo.return_value = repo
    
    # Dirty working tree (uncommitted changes)
    mock_git_manager.has_changes.return_value = True

    status = checker.check_status()
    assert status.state == RepoState.LOCAL_AHEAD

def test_status_local_ahead(mock_git_manager, mocker):
    checker = StatusChecker(mock_git_manager)
    repo = mocker.MagicMock()
    mock_git_manager.get_repo.return_value = repo
    mock_git_manager.has_changes.return_value = False

    repo.active_branch.commit = "local_hash"
    repo.active_branch.tracking_branch.return_value.commit = "remote_hash"
    
    # is_ancestor(ancestor, rev)
    # If remote is ancestor of local, Local is Ahead
    repo.is_ancestor.side_effect = lambda a, b: a == "remote_hash" and b == "local_hash"

    status = checker.check_status()
    assert status.state == RepoState.LOCAL_AHEAD

def test_status_remote_ahead(mock_git_manager, mocker):
    checker = StatusChecker(mock_git_manager)
    repo = mocker.MagicMock()
    mock_git_manager.get_repo.return_value = repo
    mock_git_manager.has_changes.return_value = False

    repo.active_branch.commit = "local_hash"
    repo.active_branch.tracking_branch.return_value.commit = "remote_hash"

    # If local is ancestor of remote, Remote is Ahead
    repo.is_ancestor.side_effect = lambda a, b: a == "local_hash" and b == "remote_hash"

    status = checker.check_status()
    assert status.state == RepoState.REMOTE_AHEAD
