from evennia import DefaultObject
from evennia.utils import delay

from server import appearance
from world.quests.quest_hooks import print_dialogue_options


class Talkable(DefaultObject):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.quest_hooks = {"at_talk": {}, "at_told": {}, "at_object_receive": {}}
        self.db.talk_responses = {}

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        super().at_object_receive(moved_obj, source_location, move_type, **kwargs)
        hooks = self.db.quest_hooks["at_object_receive"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                player = source_location
                if player.attributes.has("quest_stages") and player.quests.at_stage(qid, stage):
                    self.speak_lines(hook_data, player)

    def speak_lines(self, hook_data, player):
        """Speaks the lines from the given quest hook one-by-one, with 3 seconds between each, then advances the quest."""
        i = 0
        for line in hook_data["spoken_lines"]:
            delay(i * 3, self.say_to, player, line)
            i += 1

        delay((i-1)*3, player.quests.advance_quest, hook_data["next_stage"])
        #player.quests.advance_quest(hook_data["next_stage"])

    def at_talk(self, player):
        """
        If the player running the talk command is at the right quest stage for any at_talk hooks on this character, this
        character speaks some lines, and advances the player's quest afterward. If a matching at_talk hook is not found,
        but an at_told hook is found, the keywords for the available dialogue options will display to the player.
        Failing both of these, the NPC will run give_talk_response, giving a standard or quest-progress-specific
        message.

        :param player: The player running the talk command.
        """
        advanced = False
        hooks = self.db.quest_hooks["at_talk"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if player.quests.at_stage(qid, stage):  # Player is at a quest stage to talk to this NPC
                    self.speak_lines(hook_data, player)
                    advanced = True
                    break # Stop checking hooks. One conversation/quest per command
        if not advanced:
            # Shows dialogue options if player is at an at_told hook for this NPC (but talked instead of told)
            if not self.at_told(player, ".", from_talk=True):
                self.give_talk_response(player)  # Give a default or quest-progress-relevant greeting

    def at_told(self, teller, message: str, from_talk=False):
        """
        Checks any at_told quest hooks on this character that the speaking player is at the right quest stage for.
        These quest hooks have dialogue choice 'options', usually multiple, with keywords that the player must say in
        their message to activate that option. Each option has its own spoken lines and points to its own next quest
        stage.

        :param teller: The player running the tell command
        :param message: The message spoken by the player. Only actually parsed for keyword presence, so players can give
        realistic, roleplay-centered responses, or just give a simple command with a few words otherwise.
        :param from_talk: Whether this function is being run from the talk command, indicating the 'hmm?' should be
            suppressed if the NPC has a talk response
        :return: Boolean whether the NPC registered a dialogue option and spoke lines.
        """
        hooks = self.db.quest_hooks["at_told"]
        stage_ready = False
        spoken = False
        for qid in hooks:
            if spoken:
                break  # Stop checking hooks if we've already spoken
            for stage in hooks[qid]:
                if spoken:
                    break
                hook_data = hooks[qid][stage]
                if teller.quests.at_stage(qid, stage):  # This NPC has a hook for a quest stage this player is at
                    stage_ready = True
                    for option in hook_data["options"]:  # Dialogue options the player can say
                        all_keywords = False
                        for keyword in option["keywords"]:
                            all_keywords = True
                            if keyword not in message.split(" "):  # Keyword missing from this dialogue option
                                all_keywords = False
                        if all_keywords:
                            # All keywords in this dialogue option present in the message
                            for line in option["spoken_lines"]:
                                self.say_to(teller, line)
                            spoken = True
                            teller.quests.advance_quest(option["next_stage"])
                            break  # from options list
                    break  # Only handle one quest stage at a time
        if not spoken:
            if not from_talk:  # Skip this if we're running from at_talk so NPC's talk response is said instead
                self.say_to(teller, "Hmm?")
            if stage_ready:  # Player is at a stage to interact with this NPC, but none of the dialogue options matched
                teller.msg(
                    f"{appearance.hint}Hint: Tell {self.key} something including all keywords from one of these options:")
                teller.msg(print_dialogue_options(qid, stage))
            return False  # NPC didn't speak yet
        else:
            return True  # We initiated a conversation

    def give_talk_response(self, player):
        """
        Performs the NPC's response to the talk command. Among responses associated with the completion of quest
        stages, finds the response corresponding to the highest-number stage in the highest-number quest that the
        player talking has completed. Default responses are set to 0:0 to show to all created players.
        """
        responses = self.db.talk_responses
        if not responses:
            player.msg(self.key + " doesn't have anything to say to you.")
            return

        # Find response for highest quest stage player has completed
        sorted_qids = sorted(responses.keys(), reverse=True)

        response = None
        for qid in sorted_qids:
            if response:
                break
            stages = responses[qid]
            sorted_stage_nums = sorted(stages.keys(), reverse=True)
            for stage in sorted_stage_nums:
                if response:
                    break
                if player.db.quest_stages.get(qid, 0) >= stage:
                    response = responses[qid][stage]
        for line in response:
            self.say_to(player, line)
