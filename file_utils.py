import os
import shutil


# full filename is filename + extension
def full_filename(path: str):
    path = path.rstrip(os.sep)
    return os.path.basename(path)


# filename: without extension
def filename(path: str):
    return os.path.splitext(full_filename(path))[0]


def extension(path: str):
    return os.path.splitext(path)[1][1:]


def parent(path: str):
    path = path.rstrip(os.sep)
    return os.path.dirname(path)


def clean_path(path: str):
    return path.rstrip(os.sep)


# Move a file using os.rename
def move_file_by_copying(file_path, target_dir):
    target_path = os.path.join(target_dir, full_filename(file_path))
    shutil.copy2(file_path, target_path)


def copy_dir_to_parent_folder(dir_path, target_dir):
    target_path = os.path.join(target_dir, filename(dir_path))
    shutil.copytree(dir_path, target_path)


def move_dir_to_parent_folder(dir_path, target_dir):
    target_path = os.path.join(target_dir, filename(dir_path))
    shutil.move(dir_path, target_path)


def move_file_by_renaming(file_path, target_dir):
    target_path = os.path.join(target_dir, full_filename(file_path))
    os.rename(file_path, target_path)


def change_file_name_from_path(file_path, new_name, file_extension=None):
    if not file_extension:
        file_extension = extension(file_path)
    if filename(file_path) == new_name:
        return False
    new_path = os.path.join(parent(file_path), f'{new_name}.{file_extension}')
    os.rename(file_path, new_path)
    return True


