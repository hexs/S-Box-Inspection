import hexss

hexss.check_packages(
    'GitPython', 'AutoInspection', 'opencv-python',
    auto_install=True
)

from hexss.constants import *
from hexss.git import clone_or_pull, add, status, push
from hexss.path import get_script_dir
from hexss.threading import Multithread
from AutoInspection import training


def main():
    models = [
        # 'QD1-1985',
        'QD1-1998',  # OK
        'QD1-2001',  # OK
        'QD1-2073',  # OK
        'QC5-9973',  # OK
        'QC7-7957',  # OK
        # 'QC4-9336',
        'FE3-8546',  # OK
        # '4A3-5526',
        'QC7-2413',  # OK

        'QC7-7956-000',
        'QC5-9110-000',
        'QC5-9113-000',
        'QC7-7990-000',
        'QD1-1988-000',
        'FE4-1624-000',
        'QC8-0996-000',
    ]
    prefix = 'auto_inspection_data__'

    script_dir = get_script_dir()
    project_dir = script_dir.parent

    # Clone or pull repositories
    if hexss.system == 'Windows':
        m = Multithread()
        for model in models:
            model_folder = f'{prefix}{model}'
            m.add_func(clone_or_pull, args=(project_dir / model_folder, f'git@github.com:hexs/{model_folder}.git'))
        m.start()
        m.join()
    else:
        for model in models:
            model_folder = f'{prefix}{model}'
            try:
                clone_or_pull(project_dir / model_folder, f'git@github.com:hexs/{model_folder}.git')
            except:
                print(f"{RED}Failed to clone or pull {model_folder}{END}")
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

        file_patterns = [
            'img_full/',
            'img_frame_log/',
            'model/',
            '*.json',
            '.gitignore'
        ]
        add(model_path, file_patterns)
        s = status(model_path, file_patterns)
        push(model_path, commit_message=s if s else None)
        print()


if __name__ == '__main__':
    main()
