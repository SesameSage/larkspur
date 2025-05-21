from world.quests.quest import all_quests


class QuestHandler:
    def __init__(self, player):
        self.player = player
        self.data = self.player.db.quest_stages

    def _save(self):
        """Ensures that the handler's modified data is reflected in the player's quest data."""
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
        # Reflect in the player's data that they are now at the new stage
        self.data[qid] = stage

        # Add kill counters to player if this stage is a kill counter objective
        check_objective = True
        try:
            stage_dict = all_quests()[qid]["stages"][stage]
        except KeyError:
            check_objective = False
        if check_objective:
            if stage is not None and stage_dict["objective_type"] == "kill_counter":
                kc_dict = {"QID": qid, "stage": stage, "target_type": stage_dict["target_type"], "killed": 0,
                           "needed": stage_dict["kill_num"], "next_stage": stage_dict["next_stage"]}
                self.player.db.kill_counters.append(kc_dict)

        self._save()
