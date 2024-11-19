import os


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

