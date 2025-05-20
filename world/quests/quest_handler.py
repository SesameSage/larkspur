class QuestHandler:
    def __init__(self, player):
        self.player = player
        self.data = self.player.db.quest_stages

    def _save(self):
        self.player.db.quest_stages = self.data

    def at_stage(self, quest_hook: dict):
        """Given a quest hook dict containing a quest id and stage number, returns true if the player is currently at
        the given stage in the given quest."""
        quest = quest_hook["qid"]
        stage = quest_hook["stage"]
        if self.data.get(quest, 0) == stage:
            return True
        else:
            return False

    def advance_quest(self, quest_hook: dict):
        next_stage = quest_hook["next_stage"]
        if next_stage is not None:
            self.advance_to(quest_hook["qid"], quest_hook["next_stage"])

    def advance_to(self, qid, stage):
        self.data[qid] = stage
        self._save()
