from evennia import logger

from server import appearance
from world.quests.quest import get_stage, quest_desc
from world.quests.quest_hooks import print_dialogue_options


class QuestHandler:
    def __init__(self, player):
        self.player = player
        self._load()

    def _save(self):
        """Ensures that the handler's modified data is reflected in the player's quest data."""
        self.player.db.quest_stages = self.data

    def _load(self):
        """Update the data used in these methods based on the player's quest stage data every time the handler is
        called."""
        self.data = self.player.db.quest_stages

    def at_stage(self, qid, stage):
        """Given a quest hook dict containing a quest id and stage number, returns true if the player is currently at
        the given stage in the given quest."""
        if self.data.get(qid, 0) == stage:
            return True
        else:
            return False

    def advance_quest(self, stage_str):
        """Advance a player past a quest stage based on command-form quest-stage ID (0.0)"""
        if stage_str == "None":
            return
        numbers = stage_str.split(".")
        if len(numbers) != 2:
            logger.log_msg(f"advance_quest received a non-pair from '{stage_str}': {str(numbers)}")
            return
        qid = numbers[0]
        stage = numbers[1]
        self.advance_to(qid, stage)

    def advance_to(self, qid, stage):
        """Move the player to the given quest stage."""
        if stage is None or stage == "None":
            return
        qid = int(qid)
        stage = int(stage)

        # Reflect in the player's data that they are now at the new stage
        self.data[qid] = stage

        # Add kill counters to player if this stage is a kill counter objective
        stage_dict = get_stage(qid, stage)
        if stage_dict is not None:
            if stage_dict["objective_type"] == "kill_counter":
                kc_dict = {"QID": qid, "stage": stage, "target_type": stage_dict["target_type"], "killed": 0,
                           "needed": stage_dict["kill_num"], "next_stage": stage_dict["next_stage"]}
                self.player.db.kill_counters.append(kc_dict)

        # Notify player
        self.player.msg(f"{appearance.notify}Quest updated: {quest_desc(qid, stage)}")
        self.player.msg(print_dialogue_options(qid, stage))

        self._save()
