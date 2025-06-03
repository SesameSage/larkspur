from world.quests.quest import all_quests, get_stage


class QuestHandler:
    def __init__(self, player):
        self.player = player
        self.data = self.player.db.quest_stages

    def _save(self):
        """Ensures that the handler's modified data is reflected in the player's quest data."""
        self.player.db.quest_stages = self.data

    def at_stage(self, qid, stage):
        """Given a quest hook dict containing a quest id and stage number, returns true if the player is currently at
        the given stage in the given quest."""
        if self.data.get(qid, 0) == stage:
            return True
        else:
            return False

    def advance_quest(self, qid, stage):
        if stage is None or stage == "None":
            return
        # Reflect in the player's data that they are now at the new stage
        self.data[qid] = stage

        # Add kill counters to player if this stage is a kill counter objective
        stage_dict = get_stage(qid, stage)
        if stage_dict is not None:
            if stage_dict["objective_type"] == "kill_counter":
                kc_dict = {"QID": qid, "stage": stage, "target_type": stage_dict["target_type"], "killed": 0,
                           "needed": stage_dict["kill_num"], "next_stage": stage_dict["next_stage"]}
                self.player.db.kill_counters.append(kc_dict)

        self._save()
