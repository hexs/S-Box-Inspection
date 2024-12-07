import os
from hexss.constants.cml import *
from hexss.git import get_repositories
from hexss.path import get_script_directory, move_up
from git import Repo

selected_model = ['QC7-7990-000']


def update_repositories():
    script_directory = get_script_directory()
    projects_dir_path = move_up(script_directory)

    repositories = get_repositories("hexs")
    selected_repositories = [repo['name'] for repo in repositories if "auto_inspection_data__" in repo['name']]

    for repository_name in selected_repositories:
        model_name = repository_name.split("__")[1]
        if model_name not in selected_model:
            print(f'{BOLD}{RED}X {model_name}{ENDC}')
            continue

        print(f'{BOLD}{GREEN}/ {model_name}{ENDC}')
        project_path = os.path.join(projects_dir_path, repository_name)

        if repository_name not in os.listdir(projects_dir_path):
            print(f'\t{YELLOW}cloning... {model_name}{ENDC}')
            os.makedirs(project_path, exist_ok=True)
            repo_url = f"https://github.com/hexs/{repository_name}.git"
            Repo.clone_from(repo_url, project_path)
            print(f"\t{GREEN}clone {model_name} ok{ENDC}")
        else:
            print(f'\t{YELLOW}pulling... {model_name}{ENDC}')
            repo = Repo(project_path)
            res = repo.git.pull('origin', 'main')
            print(f'\t{res}')
            print(f"\t{GREEN}pull {model_name} ok{ENDC}")


if __name__ == "__main__":
    update_repositories()
