import git
from pathlib import Path
from typing import Optional, List

class GitManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo: Optional[git.Repo] = None
        
    def _ensure_repo(self):
        if not self.repo:
            try:
                self.repo = git.Repo(self.repo_path)
            except git.InvalidGitRepositoryError:
                raise ValueError(f"Invalid git repository at {self.repo_path}")
            except git.NoSuchPathError:
                raise ValueError(f"Path does not exist: {self.repo_path}")

    def get_repo(self) -> git.Repo:
        self._ensure_repo()
        return self.repo

    def pull(self) -> str:
        """Pulls changes from remote."""
        self._ensure_repo()
        try:
            origin = self.repo.remotes.origin
            fetch_info = origin.pull()
            if not fetch_info:
                return "No changes pulled."
            # Summarize what happened
            summary = []
            for info in fetch_info:
                summary.append(f"{info.ref}: {info.note or 'Updated'}")
            return "\n".join(summary)
        except Exception as e:
            raise RuntimeError(f"Pull failed: {e}")

    def has_changes(self) -> bool:
        """Checks if there are uncommitted changes."""
        self._ensure_repo()
        return self.repo.is_dirty(untracked_files=True)

    def commit_all(self, message: str) -> str:
        """Stages all changes and commits them."""
        self._ensure_repo()
        if not self.has_changes():
            return "No changes to commit."
        
        try:
            self.repo.git.add(A=True) # Stage all
            commit = self.repo.index.commit(message)
            return f"Committed: {commit.hexsha[:7]} - {message}"
        except Exception as e:
            raise RuntimeError(f"Commit failed: {e}")

    def push(self) -> str:
        """Pushes to remote."""
        self._ensure_repo()
        try:
            origin = self.repo.remotes.origin
            push_info_list = origin.push()
            
            # Check for errors in push info
            errors = []
            for info in push_info_list:
                if info.flags & (info.ERROR | info.REJECTED):
                    errors.append(f"Push failed for {info.remote_ref_string}: {info.summary}")
            
            if errors:
                raise RuntimeError("\n".join(errors))
            
            return "Push successful."
        except Exception as e:
            raise RuntimeError(f"Push failed: {e}")

    def get_last_remote_timestamp(self) -> Optional[float]:
        """Returns the timestamp of the last commit on the tracking branch."""
        self._ensure_repo()
        try:
            active_branch = self.repo.active_branch
            tracking_branch = active_branch.tracking_branch()
            if tracking_branch:
                return tracking_branch.commit.committed_date
            return None
        except Exception:
            return None
