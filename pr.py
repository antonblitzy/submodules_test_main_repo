#!/usr/bin/env python3
"""Cherry-pick latest PR from branch A to new branch A-X based on origin/X."""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
import re


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitOperationError(Exception):
    """Git operation failed."""
    pass


def run_git_command(
    cmd: list[str], 
    cwd: Path, 
    check: bool = True
) -> Tuple[int, str, str]:
    """Execute git command and return (returncode, stdout, stderr)."""
    logger.debug(f"Running: git {' '.join(cmd)}")
    
    result = subprocess.run(
        ['git'] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if check and result.returncode != 0:
        logger.error(f"Git command failed: {result.stderr}")
        raise GitOperationError(f"Command failed: git {' '.join(cmd)}\n{result.stderr}")
    
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_repo_config(repo_path: Path) -> Tuple[str, str]:
    """Get current user email and name from git config."""
    logger.debug("Fetching repo user config")
    
    _, email, _ = run_git_command(['config', 'user.email'], repo_path)
    _, name, _ = run_git_command(['config', 'user.name'], repo_path)
    
    if not email or not name:
        raise GitOperationError("Unable to get user email/name from git config")
    
    logger.debug(f"User: {name} <{email}>")
    return email, name


def get_remote_url(repo_path: Path) -> str:
    """Extract GitHub org/repo from remote URL."""
    logger.debug("Getting remote URL")
    
    _, url, _ = run_git_command(['remote', 'get-url', 'origin'], repo_path)
    
    # Parse GitHub URL (https or ssh format)
    match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', url)
    if not match:
        raise GitOperationError(f"Cannot parse GitHub URL: {url}")
    
    org_repo = match.group(1)
    logger.debug(f"Repository: {org_repo}")
    return org_repo


def get_latest_commit_from_branch(
    repo_path: Path, 
    branch: str, 
    author_email: str
) -> Optional[str]:
    """Get latest commit SHA from branch A by current author."""
    logger.debug(f"Finding latest commit on {branch} by {author_email}")
    
    # Get merge commits from the branch authored by user
    cmd = [
        'log',
        f'origin/{branch}',
        '--author', author_email,
        '--format=%H',
        '-n', '1'
    ]
    
    _, commit_sha, _ = run_git_command(cmd, repo_path)
    
    if not commit_sha:
        raise GitOperationError(f"No commits found on origin/{branch} by {author_email}")
    
    logger.debug(f"Found commit: {commit_sha}")
    return commit_sha


def create_branch(repo_path: Path, new_branch: str, base_branch: str) -> None:
    """Create and checkout new branch based on origin/base_branch."""
    logger.debug(f"Creating branch {new_branch} from origin/{base_branch}")
    
    # Ensure we're not on the branch we're about to create
    run_git_command(['checkout', f'origin/{base_branch}'], repo_path)
    
    # Create and checkout new branch
    run_git_command(['checkout', '-b', new_branch], repo_path)
    
    logger.debug(f"Checked out new branch: {new_branch}")


def cherry_pick_commit(repo_path: Path, commit_sha: str) -> bool:
    """Cherry-pick commit. Returns True if successful, False if conflicts."""
    logger.debug(f"Cherry-picking {commit_sha}")
    
    returncode, stdout, stderr = run_git_command(
        ['cherry-pick', commit_sha], 
        repo_path, 
        check=False
    )
    
    if returncode == 0:
        logger.debug("Cherry-pick successful")
        return True
    
    # Check if it's a conflict
    _, status, _ = run_git_command(['status', '--porcelain'], repo_path, check=False)
    
    if 'UU ' in status or 'AA ' in status or 'DD ' in status:
        logger.warning("Cherry-pick resulted in conflicts")
        return False
    
    # Other error
    raise GitOperationError(f"Cherry-pick failed: {stderr}")


def push_branch(repo_path: Path, branch: str) -> None:
    """Push branch to origin."""
    logger.debug(f"Pushing {branch} to origin")
    
    run_git_command(['push', 'origin', branch], repo_path)
    
    logger.debug("Push successful")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo_path', type=Path, help='Path to git repository')
    parser.add_argument('branch_a', help='Source branch A')
    parser.add_argument('branch_x', help='Target branch X(qa, prod)')
    
    args = parser.parse_args()
    
    repo_path = args.repo_path.resolve()
    branch_a = args.branch_a
    branch_x = args.branch_x
    new_branch = f"{branch_a}-{branch_x}"
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    if not (repo_path / '.git').exists():
        raise GitOperationError(f"Not a git repository: {repo_path}")
    
    logger.debug(f"Working with repo: {repo_path}")
    logger.debug(f"Source branch: {branch_a}, Target branch: {branch_x}")
    
    try:
        # Fetch all remotes
        print("Fetching...")
        run_git_command(['fetch', '--all'], repo_path)
        
        # Get user info and repo details
        email, name = get_repo_config(repo_path)
        org_repo = get_remote_url(repo_path)
        
        # Find latest commit from branch A
        commit_sha = get_latest_commit_from_branch(repo_path, branch_a, email)
        
        # Create new branch
        create_branch(repo_path, new_branch, branch_x)
        
        # Cherry-pick
        success = cherry_pick_commit(repo_path, commit_sha)
        
        if success:
            # Push and generate PR link
            push_branch(repo_path, new_branch)
            pr_url = f"https://github.com/{org_repo}/compare/{branch_x}...{new_branch}"
            print(pr_url)
        else:
            print("Conflicts detected. Resolve manually.")
            return 1
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
