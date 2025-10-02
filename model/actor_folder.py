from typing import Union, List


class ActorFolder:
    def __init__(self, names: Union[str, List[str]], folder_path):
        self.actor_names = []
        if names is str:
            self.actor_names = [names]
        elif names is List[str]:
            self.actor_names = names
        self.folder_path = folder_path
        