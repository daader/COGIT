from enum import Enum
from dataclasses import dataclass
from core.git import GitManager

class RepoState(Enum):
    UP_TO_DATE = "UP_TO_DATE"
    LOCAL_AHEAD = "LOCAL_AHEAD"
    REMOTE_AHEAD = "REMOTE_AHEAD"
    DIVERGED = "DIVERGED"
    ERROR = "ERROR"

@dataclass
class StatusResult:
    state: RepoState
    message: str
    last_sync: str

class StatusChecker:
    def __init__(self, git_manager: GitManager):
        self.git = git_manager

    def check_status(self) -> StatusResult:
        try:
            repo = self.git.get_repo()
            
            # Fetch explicitly to update remote refs
            repo.remotes.origin.fetch()

            # Check for uncommitted changes (dirty working tree)
            if self.git.has_changes():
                 return StatusResult(RepoState.LOCAL_AHEAD, "Uncommitted changes present.", "")

            # Get current branch
            active_branch = repo.active_branch
            tracking_branch = active_branch.tracking_branch()

            if not tracking_branch:
                return StatusResult(RepoState.ERROR, "No tracking branch configured.", "")

            # Compare commits
            local_commit = active_branch.commit
            remote_commit = tracking_branch.commit

            # Bases
            base = repo.merge_base(active_branch, tracking_branch)
            
            # Retrieve last sync time (from tracking branch)
            last_sync = ""
            ts = self.git.get_last_remote_timestamp()
            if ts:
                from datetime import datetime
                # Format: HH:MM if today, else YYYY-MM-DD
                dt = datetime.fromtimestamp(ts)
                now = datetime.now()
                if dt.date() == now.date():
                    last_sync = dt.strftime("%H:%M")
                else:
                    last_sync = dt.strftime("%Y-%m-%d %H:%M")

            if local_commit == remote_commit:
                return StatusResult(RepoState.UP_TO_DATE, "Repository is up to date.", last_sync)
            
            # Check if local is ahead
            # If remote is an ancestor of local, we are ahead
            if repo.is_ancestor(remote_commit, local_commit):
                 return StatusResult(RepoState.LOCAL_AHEAD, "You have unpushed changes.", last_sync)

            # Check if remote is ahead
            # If local is an ancestor of remote, we are behind
            if repo.is_ancestor(local_commit, remote_commit):
                return StatusResult(RepoState.REMOTE_AHEAD, "Remote has new changes.", last_sync)

            # If neither, we have diverged
            return StatusResult(RepoState.DIVERGED, "Branches have diverged.", last_sync)

        except Exception as e:
            return StatusResult(RepoState.ERROR, str(e), "")
