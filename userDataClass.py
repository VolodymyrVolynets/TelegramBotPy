class UserData():
    id: int
    isAdmin: bool
    stage: int

    def __init__(self, id: int, isAdmin: bool, stage: int):
        self.id = id
        self.isAdmin = isAdmin
        self.stage = stage