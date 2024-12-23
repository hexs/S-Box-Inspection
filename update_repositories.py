import os
import time
from hexss import json_load
from hexss.constants.cml import *
from hexss.git import get_repositories, push_if_status_change
from hexss.path import get_script_directory, move_up
from git import Repo

selected_model = json_load('config.json')['model_names']


def update_repositories():
    script_directory = get_script_directory()
    projects_dir_path = move_up(script_directory)

    repositories = get_repositories("hexs")
    selected_repositories = [repo['name'] for repo in repositories if "auto_inspection_data__" in repo['name']]

    for repository_name in selected_repositories:
        inspection_name = repository_name.split("__")[1]
        if inspection_name not in selected_model:
            print(f'{BOLD}{RED}X {inspection_name}{ENDC}')
            continue

        print(f'{BOLD}{GREEN}/ {inspection_name}{ENDC}')
        project_path = os.path.join(projects_dir_path, repository_name)

        if repository_name not in os.listdir(projects_dir_path):
            print(f'{YELLOW}cloning... {inspection_name}{ENDC}')
            os.makedirs(project_path, exist_ok=True)
            repo_url = f"https://github.com/hexs/{repository_name}.git"
            Repo.clone_from(repo_url, project_path)
            print(f"{GREEN}clone {inspection_name} ok{ENDC}")
        else:
            print(f'{YELLOW}pulling... {inspection_name}{ENDC}')
            repo = Repo(project_path)
            res = repo.git.pull('origin', 'main')
            print(f'{res}')
            print(f"{GREEN}pull {inspection_name} ok{ENDC}")

        push_if_status_change(project_path)


if __name__ == "__main__":
    while True:
        try:
            update_repositories()
            break
        except Exception as e:
            time.sleep(10)