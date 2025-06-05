from evennia import DefaultObject

from server import appearance


class Talkable(DefaultObject):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.quest_hooks.update({"at_talk": {}, "at_told": {}, "at_object_receive": {}})
        self.db.talk_responses = {}

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        super().at_object_receive(moved_obj, source_location, move_type, **kwargs)
        hooks = self.db.quest_hooks["at_object_receive"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if source_location.attributes.has("quest_stages") and source_location.quests.at_stage(qid, stage):
                    for line in hook_data["spoken_lines"]:
                        self.say_to(source_location, line)
                        # TODO: Delay in say_to lines
                    source_location.quests.advance_quest(hook_data["next_stage"])

    def at_talk(self, player):
        """
        If the player running the talk command is at the right quest stage for any at_talk hooks on this character, this
        character speaks some lines, and advances the player's quest afterward.

        :param player: The player running the talk command.
        """
        advanced = False
        hooks = self.db.quest_hooks["at_talk"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if player.quests.at_stage(qid, stage):
                    for line in hook_data["spoken_lines"]:
                        self.say_to(player, line)
                    player.quests.advance_quest(hook_data["next_stage"])
                    advanced = True
                    break
        if not advanced:
            if not self.at_told(player, ".", from_talk=True):
                self.give_talk_response(player)

    def at_told(self, teller, message: str, from_talk=False):
        """
        Checks any at_told quest hooks on this character that the speaking player is at the right quest stage for.
        These quest hooks have dialogue choice 'options', usually multiple, with keywords that the player must say in
        their message to activate that option. Each option has its own spoken lines and points to its own next quest
        stage.

        :param from_talk: Whether this function is being run from the talk command, indicating the 'hmm?' should be
            suppressed if the NPC has a talk response
        :param teller:
        :param message:
        :return:
        """
        hooks = self.db.quest_hooks["at_told"]
        stage_ready = False
        spoken = False
        for qid in hooks:
            if spoken:
                break
            for stage in hooks[qid]:
                if spoken:
                    break
                hook_data = hooks[qid][stage]
                if teller.quests.at_stage(qid, stage):
                    stage_ready = True
                    for option in hook_data["options"]:
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
            if not from_talk:
                self.say_to(teller, "Hmm?")
            if stage_ready:
                teller.msg(
                    f"{appearance.hint}Hint: Tell {self.key} something including all keywords from one of these options:")
                for option in hook_data["options"]:
                    string = "["
                    for keyword in option["keywords"]:
                        string = string + keyword + ", "
                    string = string[:-2]
                    string = string + "]"
                    teller.msg(string)
            return False
        else:
            return True

    def give_talk_response(self, player):
        """Performs the NPC's response to the talk command. Among responses associated with the completion of quest
        stages, finds the response corresponding to the highest-number stage in the highest-number quest that the
        player talking has completed."""
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
