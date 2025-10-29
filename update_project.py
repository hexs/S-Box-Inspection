import hexss

hexss.check_packages(
    'GitPython', 'AutoInspection', 'opencv-python',
    auto_install=True
)

from hexss.constants import *
from hexss.git import clone_or_pull, push_if_dirty
from hexss.path import get_script_dir
from hexss.threading import Multithread
from AutoInspection import training


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
        'QD1-2001',
        'QC7-7957'
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
            clone_or_pull(project_dir / model_folder, f'git@github.com:hexs/{model_folder}.git')
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

        push_if_dirty(model_path, [
            'img_full/',
            'img_frame_log/',
            'model/',
            '*.json'
            '.gitignore'
        ])


if __name__ == '__main__':
    main()
