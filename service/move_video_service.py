import os
import file_utils
from pathlib import Path


class MoveVideoService:
    def __init__(self, actors, target_path):
        self.actors = actors
        self.target_path = target_path
        self.favourite_path = '/Volumes/JAV'
        self.actor_name = None
        self.video_name = None
        self.file_path = None
        self.need_to_create_actor_folder = False
        self.favourite_actors = []
        self.ignore_video_paths = set()
        # read all subfolders of self.favourite_path and save them to self.favourite_actors
        for actor in os.listdir(self.favourite_path):
            if actor.startswith('.'):
                continue
            self.favourite_actors.append(actor)
        print(self.favourite_actors)

    def reset_results(self):
        self.actor_name = None
        self.video_name = None
        self.file_path = None

    def add_ignore_video(self):
        if self.file_path:
            self.ignore_video_paths.add(self.file_path)
        else:
            print('[ERROR] No file to ignore')
        self.reset_results()

    def create_actor_folder(self):
        if not self.need_to_create_actor_folder:
            return
        target_actor_path = self._get_target_actor_path()
        if not os.path.exists(target_actor_path):
            os.makedirs(target_actor_path)
            print(f'Created folder {target_actor_path}')
        else:
            print(f'[ERROR] Folder {target_actor_path} already exists')

    def move_video(self):
        if not self.video_name:
            return
        target_actor_path = self._get_target_actor_path()
        self._move_file(self.file_path, target_actor_path)
        print(f'Moved file {self.file_path} to {target_actor_path}')
        self.reset_results()

    def _get_target_actor_path(self):
        if self.actor_name in self.favourite_actors:
            target_actor_path = os.path.join(self.favourite_path, self.actor_name)
        else:
            target_actor_path = os.path.join(self.target_path, self.actor_name)
        return target_actor_path


    def process_files(self, file_paths):
        for file_path in file_paths:
            if file_path in self.ignore_video_paths:
                continue
            self.need_to_create_actor_folder = self._process_file(file_path)
            return self.need_to_create_actor_folder
            # if not result:
            #     print(f'File {file_path} not moved. Actor {self.actor_name} not found')
            #     return False
        return True

    def _process_file(self, file_path):
        video_name = Path(file_path).name
        print(video_name)
        actors = set()
        for actor in self.actors:
            if actor in video_name:
                actors.add(actor)
        self.file_path = file_path
        self.video_name = video_name
        if len(actors) > 0:
            actor = actors.pop()
            target_actor_path = os.path.join(self.target_path, actor)
            self.actor_name = actor
            return not os.path.exists(target_actor_path)

    def _move_file(self, file_path, target_folder):
        # judge if on same disk
        if target_folder.startswith('/Volumes/') and not file_path.startswith('/Volumes/'):
            # move local file to smb disk
            print('start to move file to smb disk')
            file_utils.move_dir_to_parent_folder(file_path, target_folder)
        else:
            print('start to move file by renaming')
            file_utils.move_file_by_renaming(file_path, target_folder)



