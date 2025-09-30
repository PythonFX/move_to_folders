import os
import file_utils
import string_utils
from exceptions import MultipleVideoNumberMatch, NoVideoNumberMatch


class RenameService:
    def __init__(self):
        pass

    def rename_files(self, file_paths):
        file_paths = [path for path in file_paths if not os.path.isdir(path)]
        video_extensions = ['mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm']
        video_files = [file for file in file_paths if file_utils.extension(file).lower() in video_extensions]

        for video_path in video_files:
            file_name = file_utils.filename(video_path)
            try:
                video_number = string_utils.get_video_number_with_tags(video_path)
                is_changed = file_utils.change_file_name_from_path(video_path, video_number)
                if is_changed:
                    print(f'[rename] {file_name} --> {video_number}')
            except (MultipleVideoNumberMatch, NoVideoNumberMatch) as e:
                print(f"Match Error: {str(e)} for {file_name}")
            except Exception as e:
                print(f"Unknown Error: {e}")





