class QuestHandler:
    def __init__(self, player):
        self.player = player
        self._save()

    def _save(self):
        self.data = self.player.attributes.get("quest_stages", default={})

    def at_stage(self, quest_hook: dict):
        """Given a quest hook dict containing a quest id and stage number, returns true if the player is currently at
        the given stage in the given quest."""
        quest = quest_hook["qid"]
        stage = quest_hook["stage"]
        if self.data[quest] == stage:
            return True
        else:
            return False

    def advance_quest(self, quest_hook: dict):
        self.advance_to(quest_hook["qid"], quest_hook["next_stage"])

    def advance_to(self, qid, stage):
        self.data[qid] = stage
        self._save()
