


class MultipleVideoNumberMatch(Exception):
    def __init__(self, message="Multiple video numbers matched"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class NoVideoNumberMatch(Exception):
    def __init__(self, message="No video numbers matched"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
