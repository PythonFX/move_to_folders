import os
import file_utils


class OrganizeFileService:
    def __init__(self):
        pass

    def sort_and_organize_files(self, file_paths):
        # ignore folder path
        file_paths = [path for path in file_paths if not os.path.isdir(path)]

        # Define the file extensions for videos and images
        video_extensions = ['mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm']
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

        # Separate the file paths into videos and images
        video_files = [file for file in file_paths if file_utils.extension(file).lower() in video_extensions]
        image_files = [file for file in file_paths if file_utils.extension(file).lower() in image_extensions]

        # Function to create a directory if it doesn't exist
        def create_dir_if_not_exists(dir_name):
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

        def get_folder_name(s, is_4k):
            last_dot_index = s.rfind('.')
            if last_dot_index != -1:
                folder_name = s[:last_dot_index]
            else:
                folder_name = s
            if is_4k:
                first_space_index = folder_name.find(' ')
                if first_space_index != -1:
                    # insert '[4K]' at position first_space_index
                    folder_name = folder_name[:first_space_index] + '[4K]' + folder_name[first_space_index:]
            return folder_name

        def get_video_prefix(video):
            filename = file_utils.filename(video)
            # remove leading bracket and everything in it
            if filename.startswith('['):
                closing_bracket_index = filename.find(']')
                if closing_bracket_index != -1:
                    filename = filename[closing_bracket_index + 1:]
                    print(f'cleaned filename = {filename}')
            if filename.startswith('【'):
                closing_bracket_index = filename.find('】')
                if closing_bracket_index != -1:
                    filename = filename[closing_bracket_index + 1:]
                    print(f'cleaned filename = {filename}')
            return filename[:prefix_len].lower()

        # Iterate over each image file
        for image in image_files:
            image_name = file_utils.full_filename(image)
            first_space_idx = image_name.find(' ')
            if first_space_idx == -1:
                prefix_len = 8  # like ABP-986
            else:
                prefix_len = first_space_idx
            image_prefix = image_name.split('.')[0][:prefix_len].lower()
            print(f'image_prefix = {image_prefix}')
            found_video = False

            # Iterate over each video file to find a match
            for video in video_files:
                video_prefix = get_video_prefix(video)
                print(f'video_prefix = {video_prefix}')
                if image_prefix == video_prefix:
                    if '4k2' in video:
                        video = video.replace('4k2', '3k2')
                    folder_name = get_folder_name(os.path.basename(image), '4k' in video or '4K' in video)
                    parent_folder_path = os.path.dirname(image)
                    folder_path = os.path.join(parent_folder_path, folder_name)
                    create_dir_if_not_exists(folder_path)
                    file_utils.move_file_by_renaming(image, folder_path)
                    file_utils.move_file_by_renaming(video, folder_path)
                    video_files.remove(video)
                    found_video = True
                    break

            if not found_video:
                print(f'No video found for {os.path.basename(image)}')
