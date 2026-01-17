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
        """Pushes to remote, automatically syncing if remote has unpulled changes.
        
        If there are unpulled remote changes, uses stash-pull-pop workflow
        to merge local changes with remote. Otherwise, just pushes normally.
        """
        self._ensure_repo()
        messages = []
        
        try:
            origin = self.repo.remotes.origin
            
            # Fetch to check if remote has changes
            origin.fetch()
            
            # Check if remote is ahead of local
            active_branch = self.repo.active_branch
            tracking_branch = active_branch.tracking_branch()
            
            remote_ahead = False
            if tracking_branch:
                local_commit = self.repo.head.commit
                remote_commit = tracking_branch.commit
                # Check if remote has commits we don't have
                remote_ahead = local_commit != remote_commit and \
                    remote_commit not in self.repo.merge_base(local_commit, remote_commit)
            
            # Only do stash-pull-pop if remote is ahead
            if remote_ahead:
                had_stash = False
                
                # Step 1: Stash local changes if any exist
                if self.repo.is_dirty(untracked_files=True):
                    self.repo.git.stash('push', '-u', '-m', 'Auto-stash before sync')
                    had_stash = True
                    messages.append("Stashed local changes.")
                
                # Step 2: Pull remote changes
                try:
                    origin.pull()
                    messages.append("Pulled remote changes.")
                except Exception as pull_error:
                    # If pull fails and we stashed, try to restore
                    if had_stash:
                        try:
                            self.repo.git.stash('pop')
                        except:
                            pass
                    raise RuntimeError(f"Pull failed during sync: {pull_error}")
                
                # Step 3: Pop stash to merge local changes back
                if had_stash:
                    try:
                        self.repo.git.stash('pop')
                        messages.append("Restored local changes.")
                    except Exception as stash_error:
                        raise RuntimeError(
                            f"Merge conflict while restoring local changes: {stash_error}\n"
                            "Your changes are still saved in the stash. "
                            "Run 'git stash pop' manually to resolve conflicts."
                        )
            
            # Step 4: Push to remote
            push_info_list = origin.push()
            
            # Check for errors in push info
            errors = []
            for info in push_info_list:
                if info.flags & (info.ERROR | info.REJECTED):
                    errors.append(f"Push failed for {info.remote_ref_string}: {info.summary}")
            
            if errors:
                raise RuntimeError("\n".join(errors))
            
            messages.append("Push successful.")
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
