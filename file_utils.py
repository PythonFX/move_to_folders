import os
import shutil
from pathlib import Path


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


def clean_video_filename(full_file_name: str, folder_path: str):
    original_file_name = full_file_name
    # try split file by @, typical examples:
    # [activehlj.com]@FSDSS-783_[4K].mkv
    # 169bbs.com@FSDSS-932_[4K].mkv
    file_name = filename(full_file_name)
    ext = extension(full_file_name)
    
    if '@' in file_name:
        parts = file_name.split('@')
        if len(parts) == 2:
            if '.com' in parts[0] or '.net' in parts[0]:
                file_name = parts[1]
            elif '.com' in parts[1] or '.net' in parts[1]:
                file_name = parts[0]
            full_file_name = f'{file_name}.{ext}'
    # rename to new name
    if full_file_name != original_file_name:
        os.rename(os.path.join(folder_path, original_file_name), os.path.join(folder_path, full_file_name))
    return os.path.join(folder_path, full_file_name)
    
    
def is_4k_video(video: str):
    temp_video = video.replace('4k2', '3k2')
    return '4k' in temp_video or '4K' in temp_video


def has_video_under_path(folder_path: str):
    if not os.path.isdir(folder_path):
        return False
    video_extensions = {'mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm'}
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        return False
    
    return any(
        file.suffix.lower().lstrip('.') in video_extensions
        for file in folder.iterdir()
        if file.is_file()
    )


# Move a file using os.rename
def move_file_by_copying(file_path, target_dir):
    target_path = os.path.join(target_dir, full_filename(file_path))
    shutil.copy2(file_path, target_path)


def copy_dir_to_parent_folder(dir_path, target_dir):
    target_path = os.path.join(target_dir, filename(dir_path))
    shutil.copytree(dir_path, target_path)


# this is redundant, could just use shutil.move(dir_path, target_dir)
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


