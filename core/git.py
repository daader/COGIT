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

    def _abort_merge_if_needed(self):
        """Aborts any stuck merge operations."""
        try:
            merge_head = self.repo_path / '.git' / 'MERGE_HEAD'
            if merge_head.exists():
                self.repo.git.merge('--abort')
                return True
        except Exception:
            pass
        return False

    def _reset_to_clean_state(self):
        """Resets repo to a clean state, aborting merges and clearing conflicts."""
        self._abort_merge_if_needed()
        try:
            # Reset any staged changes that might be causing issues
            self.repo.git.reset('--mixed', 'HEAD')
        except Exception:
            pass

    def pull(self) -> str:
        """Pulls changes from remote. Forces sync if there are conflicts."""
        self._ensure_repo()
        messages = []
        
        # Abort any stuck merge first
        if self._abort_merge_if_needed():
            messages.append("Aborted stuck merge.")
        
        try:
            origin = self.repo.remotes.origin
            
            # Stash any local changes before pull
            had_stash = False
            if self.repo.is_dirty(untracked_files=True):
                try:
                    self.repo.git.stash('push', '-u', '-m', 'Auto-stash before pull')
                    had_stash = True
                    messages.append("Stashed local changes.")
                except Exception:
                    pass
            
            try:
                fetch_info = origin.pull()
                if fetch_info:
                    for info in fetch_info:
                        messages.append(f"{info.ref}: {info.note or 'Updated'}")
                else:
                    messages.append("Already up to date.")
            except Exception as pull_error:
                # If normal pull fails, try force reset to remote
                messages.append("Normal pull failed, force syncing to remote...")
                try:
                    origin.fetch()
                    active_branch = self.repo.active_branch
                    tracking_branch = active_branch.tracking_branch()
                    if tracking_branch:
                        self.repo.git.reset('--hard', tracking_branch.name)
                        messages.append("Force synced to remote.")
                    else:
                        raise pull_error
                except Exception:
                    raise RuntimeError(f"Pull failed: {pull_error}")
            
            # Restore stashed changes
            if had_stash:
                try:
                    self.repo.git.stash('pop')
                    messages.append("Restored local changes.")
                except Exception:
                    # If stash pop fails due to conflicts, drop the stash
                    messages.append("Could not auto-merge stashed changes, keeping remote version.")
                    try:
                        self.repo.git.stash('drop')
                    except Exception:
                        pass
            
            return "\n".join(messages) if messages else "Pull complete."
        except RuntimeError:
            raise
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
        """Pushes to remote. Uses force push if normal push fails.
        
        For single-user workflow: always ensures push succeeds.
        """
        self._ensure_repo()
        messages = []
        
        # Abort any stuck merge first
        if self._abort_merge_if_needed():
            messages.append("Aborted stuck merge.")
        
        try:
            origin = self.repo.remotes.origin
            active_branch = self.repo.active_branch
            
            # Try normal push first
            try:
                push_info_list = origin.push()
                
                # Check for errors in push info
                push_failed = False
                for info in push_info_list:
                    if info.flags & (info.ERROR | info.REJECTED):
                        push_failed = True
                        break
                
                if not push_failed:
                    messages.append("Push successful.")
                    return "\n".join(messages) if messages else "Push successful."
            except Exception:
                push_failed = True
            
            # If normal push failed, force push
            if push_failed:
                messages.append("Normal push failed, using force push...")
                try:
                    origin.push(force=True)
                    messages.append("Force push successful.")
                except Exception as force_error:
                    raise RuntimeError(f"Force push failed: {force_error}")
            
            return "\n".join(messages)
            
        except RuntimeError:
            raise
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
