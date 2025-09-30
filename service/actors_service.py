import os


class ActorsService:
    def __init__(self):
        self.path = "/Users/vincent/Downloads/actor_names.txt"
        self.actors = []
        with open(self.path, "r") as f:
            self.actors = f.read().splitlines()
