from commands.character_cmdsets import PlayerCmdSet
from commands.refiled_cmds import RefiledCmdSet
from server import appearance
from stats.char_stats import xp_threshold
from typeclasses.living.characters import Character
from stats.stats_constants import BASE_CARRY_WEIGHT, STR_TO_CARRY_WEIGHT, BASE_CARRY_COUNT
from typeclasses.scripts.player_scripts import LevelUpReminder
from world.locations import rooms


class PlayerCharacter(Character):
    """A character intended to be played by a user. """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.unique_name = True
        self.permissions.add("Player")
        self.db.dies = False

        if not self.attributes.has("xp"):
            self.db.xp = 0
        if not self.attributes.has("attr_points"):
            self.db.attr_points = 0

        if not self.attributes.has("portal_keys"):
            self.db.portal_keys = []

        self.db.carry_weight = BASE_CARRY_WEIGHT
        self.db.max_carry_count = BASE_CARRY_COUNT
        # TODO: Story point and portal key handler

        if not self.attributes.has("prefs", category="ooc"):
            self.attributes.add(key="prefs", value={"more_info": False}, category="ooc")

        self.cmdset.add(PlayerCmdSet, persistent=True)
        self.cmdset.add(RefiledCmdSet, persistent=True)  # Override player cmds where necessary

        self.update_base_stats()

    # <editor-fold desc="Appearance">
    def color(self):
        return appearance.player

    def at_look(self, target=None, session=None, **kwargs):
        if isinstance(target, rooms.Room):
            self.execute_cmd("map")
        return super().at_look(target, **kwargs)

    def cmd_format(self, string):
        return appearance.cmd + "'" + string + "'|n"
    # </editor-fold>

    # <editor-fold desc="Messaging">
    def print_ambient(self, string):
        self.msg(appearance.ambient + string)

    def print_hint(self, string):
        self.msg(appearance.hint + "Hint: " + string)

    def more_info(self, string):
        if self.attributes.get("prefs", category="ooc")["more_info"]:
            self.msg(appearance.moreinfo + string)

    def at_post_move(self, source_location, move_type="move", **kwargs):
        super().at_post_move(source_location, move_type, **kwargs)
        if self.location.db.is_outdoors and not source_location.db.is_outdoors:
            self.print_ambient(self.location.zone().db.current_weather["ongoing_msg"])
    # </editor-fold>

    # <editor-fold desc="Stats">
    def update_base_stats(self):
        super().update_base_stats()
        self.db.carry_weight = BASE_CARRY_WEIGHT + STR_TO_CARRY_WEIGHT[self.get_attr("str")]

    def gain_xp(self, amt):
        self.db.xp += amt
        self.msg(f"|345You gain {amt} experience!")
        if self.db.xp >= xp_threshold(self.db.level + 1):
            self.scripts.add(LevelUpReminder())

    def level_up(self):
        self.update_base_stats()

    def meets_level_requirement(self, target):
        # Abilities
        if target.db.cooldown:
            ability_tree = self.db.rpg_class.ability_tree
            for level in range(self.db.level + 1):
                if level == 0:
                    continue
                if type(target) in ability_tree[level]:
                    return True
            return False

    def meets_attr_requirements(self, target):
        # Abilities
        if target.db.cooldown:
            for stat, amount in target.db.requires:
                # Use the base character attribute, not the effective value from equipment, etc
                if self.db.attribs[stat] < amount:
                    return False
            return True
    # </editor-fold>
