from typeclasses.scripts.scripts import Script


class Quest(Script):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.qid = None
        self.db.recommended_level = None
        self.db.stages = {}  # Number: objective
