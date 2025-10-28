from pathlib import Path
from typing import List, Optional

import hexss

hexss.check_packages(
    'GitPython', 'AutoInspection',
    auto_install=True
)

from git import Repo, GitCommandError
from hexss.constants import *
from hexss.path import get_script_dir, ascend_path
from AutoInspection import training


def clone_repo(path: Path, url: str) -> Optional[Path]:
    """
    Clone a git repository to the specified path.
    Returns the path to the cloned repo, or None on error.
    """
    try:
        print(f"{YELLOW}Cloning repository from {url} into {path}...{END}")
        repo = Repo.clone_from(url, str(path))
        print(f"{GREEN}Repository successfully cloned to: {repo.working_dir}{END}")
        return Path(repo.working_dir)
    except GitCommandError as e:
        print(f"{RED}Git error while cloning repository:{END} {e}")
    except Exception as e:
        print(f"{RED}Unexpected error while cloning repository:{END} {e}")
    return None


def pull_repo(path: Path) -> bool:
    """
    Pull changes from the 'main' branch of the git repository at path.
    Returns True if successful, False otherwise.
    """
    try:
        repo = Repo(str(path))
        repo.git.checkout('main')
        res = repo.git.pull('origin', 'main')
        print(f"{GREEN}Pulled: {res}{END}")
        return True
    except GitCommandError as e:
        print(f"{RED}Git error while pulling changes in {path}:{END} {e}")
    except Exception as e:
        print(f"{RED}Unexpected error while pulling changes in {path}:{END} {e}")
    return False


def find_model_dirs(project_dir: Path, prefix: str = 'auto_inspection_data__') -> List[Path]:
    """
    Returns a list of directories in project_dir whose names start with the given prefix.
    """
    return [p for p in project_dir.iterdir() if p.is_dir() and p.name.startswith(prefix)]


def get_repo_status(repo: Repo) -> List[str]:
    """
    Returns a list of status lines from 'git status --porcelain'.
    """
    return repo.git.status('--porcelain').splitlines()


def parse_status_lines(status_lines: List[str]) -> str:
    """
    Parses the status lines to a readable commit message.
    """
    status_map = {
        "M": "modified",
        "A": "added",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "U": "updated",
        "?": "untracked"
    }
    details = []
    for line in status_lines:
        code = line[:2].strip()
        file_path = line[3:].strip()
        if code:
            status_key = status_map.get(code[0], code)
            details.append(f"{status_key} {file_path}")
    return ", ".join(details)


def stage_and_commit(repo: Repo, model_path: Path, details: str) -> bool:
    """
    Stages relevant files and directories, commits with the provided details, and pushes to origin/main.
    """
    try:
        repo.git.checkout('main')

        # Stage folders if they exist
        for folder_or_file in ['model/', 'img_full/', 'img_frame_log/']:
            full_path = model_path / folder_or_file
            if full_path.exists():
                repo.git.add(str(full_path))
        # Stage all .json files
        for json_file in model_path.glob('*.json'):
            repo.git.add(str(json_file))
        # Commit and push
        print(f"{YELLOW}Committing: {details}{END}")
        repo.git.commit('-m', details)
        print(f"{YELLOW}Pushing to origin/main...{END}")
        repo.git.push('origin', 'main')
        print(f"{GREEN}Committed and pushed: {details}{END}")
        return True
    except GitCommandError as e:
        print(f"{RED}Git error during commit/push:{END} {e}")
    except Exception as e:
        print(f"{RED}Unexpected error during commit/push:{END} {e}")
    return False


def main():
    models = [
        'QC7-7956-000',
        'QC5-9110-000',
        'QC5-9113-000',
        'QC7-7990-000',
        'QD1-1988-000',
        'FE4-1624-000',
        'QC8-0996-000',

        'QD1-1998',
        'QC5-9973',
        'FE3-8546',
        'QC7-7957'
    ]
    prefix = 'auto_inspection_data__'

    script_dir = get_script_dir()
    project_dir = script_dir.parent
    model_dirs = find_model_dirs(project_dir)
    model_dir_names = {p.name for p in model_dirs}

    # Clone or pull repositories
    for model in models:
        model_folder = f'{prefix}{model}'
        model_path = project_dir / model_folder
        if model_folder in model_dir_names:
            print(f"{YELLOW}Pulling {model_folder}{END}")
            pull_repo(model_path)
        else:
            print(f"{YELLOW}Cloning {model_folder}{END}")
            url = f'https://github.com/hexs/{model_folder}.git'
            clone_repo(model_path, url)
        print()

    # Training
    if hexss.system == 'Windows':
        try:
            training(
                *models,
                config={
                    'projects_directory': str(project_dir),
                    'batch_size': 32,
                    'img_height': 180,
                    'img_width': 180,
                    'epochs': 8,
                    'shift_values': [-4, -2, 0, 2, 4],
                    'brightness_values': [-24, -12, 0, 12, 24],
                    'contrast_values': [-12, -6, 0, 6, 12],
                    'max_file': 20000,
                }
            )
        except Exception as e:
            print(f"{RED}Error during training:{END} {e}")
        print()

    # Commit and push changes for each repo
    for model in models:
        model_folder = f'{prefix}{model}'
        model_path = project_dir / model_folder
        print(f"{CYAN}{model_path}:{END}")
        try:
            repo = Repo(str(model_path))
        except Exception as e:
            print(f"{RED}Could not open repo at {model_path}:{END} {e}")
            continue

        status_lines = get_repo_status(repo)
        if not status_lines:
            print(f"{GREEN}No changes to commit.{END}")
            continue

        details = parse_status_lines(status_lines)
        # details = f"({'),('.join(status_lines)})"
        if details:
            ...
            stage_and_commit(repo, model_path, details)
        else:
            print(f"{GREEN}No relevant changes detected for {model_folder}.{END}")


if __name__ == '__main__':
    main()
