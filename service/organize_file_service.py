import os
import shutil

import file_utils
from model.actor_folder import ActorFolder


class OrganizeFileService:
    def __init__(self):
        self.actor_names = []
        self.actors = {}  # key: actor_name, value: ActorFolder
        self.xsk_path = '/Volumes/XSK'
        self.jav_path = '/Volumes/JAV'
        self.load_actors()
        self.processed_folders = set()

    def load_actors(self):
        try:
            self._load_actors_in_path(self.xsk_path)
            self._load_actors_in_path(self.jav_path)
            self._update_actor_names()
        except Exception as e:
            print(str(e))
        
    def _update_actor_names(self):
        self.actor_names = list(self.actors.keys())
        # reverse so that 葵つかさ is ahead of 葵 to avoid common mistake
        self.actor_names = sorted(self.actor_names, reverse=True)
        
    def _load_actors_in_path(self, root_path):
        for name in os.listdir(root_path):
            if name == '#recycle' or '==' in name:
                continue
            path = os.path.join(root_path, name)
            if not os.path.isdir(path):
                continue
            if '(' in name and ')' in name:
                # double actor names for this folder
                parts = name.split('(')
                parts[1] = parts[1].replace(')', '')
                # print(parts)
                actor_folder = ActorFolder(parts, path)
                self.actors[parts[0]] = actor_folder
                self.actors[parts[1]] = actor_folder
            else:
                self.actors[name] = ActorFolder(name, path)
    
    def start_move_video_folder(self, folder_paths, video_label, actor_entry):
        filtered_folders = []
        for folder_path in folder_paths:
            if file_utils.has_video_under_path(folder_path):
                filtered_folders.append(folder_path)
        folder_paths = filtered_folders
        print(folder_paths)
        for folder_path in folder_paths:
            if folder_path in self.processed_folders:
                continue
            folder_name = file_utils.full_filename(folder_path)
            has_found_actor = False
            self.processed_folders.add(folder_path)
            video_label.setText(folder_name)
            for actor_name in self.actor_names:
                if actor_name in folder_name:
                    print(f'{actor_name} found in {folder_name}')
                    actor_entry.setText(actor_name)
                    actor = self.actors[actor_name]
                    print(f'start moving {folder_path} to\n\t{actor.folder_path}')
                    return
            print(f'actor not found for {folder_name}')
            folder_parts = folder_name.split(' ')
            last_part = folder_parts[-1]
            actor_entry.setText(f'{last_part}==')
            break
    
    def confirm_move_video_folder(self, folder_name: str, actor_name: str, source_parent_folder: str, actor_entry):
        # check actor name is valid
        if actor_name == '0':
            actor_name = '==合集=='
        if '==合集==' != actor_name and '==' in actor_name:
            print('actor name invalid')
            return
        if actor_name not in self.actor_names:
            print(f'{actor_name} is not valid actor name, to create one')
            # add this actor to self.xsk_path
            new_folder = os.path.join(self.xsk_path, actor_name)
            os.makedirs(new_folder, exist_ok=True)
            # add new actor to self.actors
            new_actor = ActorFolder(actor_name, new_folder)
            self.actors[actor_name] = new_actor
            self._update_actor_names()
            print(f'{new_folder} created')
            
        actor = self.actors[actor_name]
        source_video_folder_path = os.path.join(source_parent_folder, folder_name)
        target_parent_path = actor.folder_path
        print(f'confirm_move_video_folder: \n\t{source_video_folder_path}\n\t{target_parent_path}')
        target_path = os.path.join(target_parent_path, folder_name)
        if os.path.exists(target_path):
            print('[ERROR] target video folder exists! No Move!')
            actor_entry.setText('==[ERROR] Exist==')
            return
        shutil.move(source_video_folder_path, target_parent_path)
        actor_entry.setText('==Move Finish==')

    def sort_and_organize_files(self, file_paths):
        # ignore folder path
        file_paths = [path for path in file_paths if not os.path.isdir(path)]

        # Define the file extensions for videos and images
        video_extensions = ['mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm']
        image_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'webp']

        # Separate the file paths into videos and images
        video_files = [file for file in file_paths if file_utils.extension(file).lower() in video_extensions]
        image_files = [file for file in file_paths if file_utils.extension(file).lower() in image_extensions]
        
        # clean video file names
        cleaned_video_files = []
        for video in video_files:
            folder_path = file_utils.parent(video)
            cleaned_video = file_utils.clean_video_filename(file_utils.full_filename(video), folder_path)
            cleaned_video_files.append(cleaned_video)
        video_files = cleaned_video_files

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
                    image_file_name = os.path.basename(image)
                    video_file_name = file_utils.full_filename(video)
                    folder_name = get_folder_name(image_file_name, file_utils.is_4k_video(video))
                    parent_folder_path = os.path.dirname(image)
                    folder_path = os.path.join(parent_folder_path, folder_name)
                    create_dir_if_not_exists(folder_path)
                    file_utils.move_file_by_renaming(image, folder_path)
                    file_utils.move_file_by_renaming(video, folder_path)
                    # rename image file to number name
                    
                    number_name = image_prefix.upper()
                    os.rename(os.path.join(folder_path, image_file_name),
                              os.path.join(folder_path, f'{number_name}.jpg'))
                    # rename video file to number name
                    ext = file_utils.extension(video)
                    os.rename(os.path.join(folder_path, video_file_name),
                              os.path.join(folder_path, f'{number_name}.{ext}'))
                    
                    video_files.remove(video)
                    found_video = True
                    break

            if not found_video:
                print(f'No video found for {os.path.basename(image)}')
